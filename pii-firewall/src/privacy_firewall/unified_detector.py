"""Unified detection engine integrating all detection backends."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
import sys
from typing import Any

_logger = logging.getLogger(__name__)

from .types import Entity
from .language import LanguageDetector, ThreadLanguageCache, LanguageRouter
from .patterns import PatternCatalog, create_default_catalog
from .profiles import DomainProfile
from . import entity_types as ET


# Canonical mapping from GLiNER label strings → internal entity type constants.
# GLiNER uses free-text labels — keep this in sync with the labels passed to
# predict_entities() in _detect_with_gliner().
GLINER_LABEL_TO_ENTITY: dict[str, str] = {
    "name":                  ET.PERSON,
    "first name":            ET.PERSON,
    "last name":             ET.PERSON,
    "email address":         ET.EMAIL,
    "phone number":          ET.PHONE_NUMBER,
    "location address":      ET.ADDRESS,
    "location city":         ET.LOCATION,
    "location state":        ET.LOCATION,
    "location country":      ET.LOCATION,
    "location zip":          ET.POSTAL_CODE,
    "dob":                   ET.DATE_TIME,
    "date of birth":         ET.DATE_TIME,
    "date":                  ET.DATE_TIME,
    "passport number":       ET.PASSPORT,
    "driver license":        ET.DRIVERS_LICENSE,
    "ssn":                   ET.SSN,
    "national id":           ET.NATIONAL_ID,
    "tax id":                ET.TAX_ID,
    "medical record number": ET.MEDICAL_RECORD,
    "healthcare number":     ET.MEDICAL_RECORD,
    "account number":        ET.ACCOUNT_NUMBER,
    "bank account":          ET.ACCOUNT_NUMBER,
    "routing number":        ET.ACCOUNT_NUMBER,
    "credit card":           ET.CREDIT_CARD,
    "url":                   ET.URL,
    "ip address":            ET.IP_ADDRESS,
    "username":              ET.SECRET,
    "password":              ET.SECRET,
    "api key":               ET.SECRET,
}


@dataclass
class UnifiedDetectionEngine:
    """Unified detection engine that combines all detection methods.
    
    This orchestrates:
    - Language detection (with caching)
    - Pattern-based detection (locale-aware)
    - Presidio NER (context-aware)
    - OpenAI Privacy Filter (token classification)
    - Transformer NER (domain-specific)
    - Linguistic false-positive filtering
    - Domain profile filtering
    
    Attributes:
        profile: Domain profile (determines which entities to detect)
        language_detector: Language detector (or None for manual language)
        language_cache: Thread-level language cache (or None to disable)
        language_router: Routes language to NLP engines
        pattern_catalog: Pattern catalog for regex detection
        detector_backend: "presidio", "opf", "gliner", "nemotron", "transformers", or "hybrid"
        custom_recognizers: Custom Presidio recognizers to add
    """
    
    profile: DomainProfile
    language_detector: LanguageDetector | None = None
    language_cache: ThreadLanguageCache | None = None
    language_router: LanguageRouter | None = None
    pattern_catalog: PatternCatalog | None = None
    detector_backend: str = "regex"  # "presidio", "opf", "gliner", "nemotron", "transformers", "hybrid", "regex"
    custom_recognizers: list[Any] = field(default_factory=list)
    transformer_model_id: str | None = None
    transformer_device: int = -1
    gliner_model_id: str = "knowledgator/gliner-pii-base-v1.0"
    opf_checkpoint: str | None = None
    
    # Internal state - engines cached by language
    _presidio_engines: dict[str, Any] = field(default_factory=dict, init=False, repr=False)
    _opf_engine: Any = field(default=None, init=False, repr=False)
    _nemotron_engine: Any = field(default=None, init=False, repr=False)
    _gliner_engine: Any = field(default=None, init=False, repr=False)
    _transformer_engines: dict[str, Any] = field(default_factory=dict, init=False, repr=False)
    _linguistic_filters: dict[str, Any] = field(default_factory=dict, init=False, repr=False)
    
    def __post_init__(self) -> None:
        supported_backends = {"regex", "presidio", "opf", "gliner", "nemotron", "transformers", "hybrid"}
        if self.detector_backend not in supported_backends:
            raise ValueError(
                f"Unsupported detector_backend '{self.detector_backend}'. "
                f"Supported: {sorted(supported_backends)}"
            )

        # Initialize defaults
        if self.language_router is None:
            from .language import LanguageRouter
            self.language_router = LanguageRouter()
        
        if self.pattern_catalog is None:
            self.pattern_catalog = create_default_catalog()
        
        if self.language_detector is None:
            try:
                from .language import LanguageDetector
                self.language_detector = LanguageDetector()
            except ImportError:
                # OK if None - will use manual language in detect()
                pass
        
        # Don't initialize backends yet - lazy load on first use
    
    def detect(
        self,
        text: str,
        language: str | None = None,
        thread_id: str | None = None,
        context_words: list[str] | None = None,
    ) -> tuple[list[Entity], str]:
        """Detect all entities in text.
        
        Args:
            text: Input text
            language: Language code (or None to auto-detect)
            thread_id: Thread ID for language caching
            context_words: Context words to boost detection
        
        Returns:
            (detected_entities, detected_language)
        """
        # Step 1: Detect language
        detected_language = self._detect_language(text, language, thread_id)

        # Step 2: Get locale for pattern routing
        locale = self.language_router.get_patterns_locale(detected_language)

        _logger.info(
            "[detect] profile=%s backend=%s lang=%s locale=%s text=%r",
            self.profile.name, self.detector_backend, detected_language, locale,
            text[:120] + ("..." if len(text) > 120 else ""),
        )

        # Prime linguistic filter early so first-pass trim/merge can use it.
        if self.profile.linguistic_filter_enabled:
            self._ensure_linguistic_filter(detected_language)

        # Step 3: Detect with all backends
        entities: list[Entity] = []

        # Pattern-based detection (works for all languages)
        pattern_entities = self._detect_with_patterns(text, locale)
        _logger.info("[pattern] %d entities: %s", len(pattern_entities),
                     [(e.entity_type, repr(e.text)) for e in pattern_entities])
        entities.extend(pattern_entities)

        # NER-based detection with Presidio (works for all languages via SpacyRecognizer)
        if self.detector_backend in ("presidio", "hybrid"):
            presidio_entities = self._detect_with_presidio(text, detected_language, context_words)
            _logger.info("[presidio] %d entities: %s", len(presidio_entities),
                         [(e.entity_type, repr(e.text)) for e in presidio_entities])
            entities.extend(presidio_entities)

        # OPF-based detection (language-agnostic token classifier)
        if self.detector_backend == "opf":
            opf_entities = self._detect_with_opf(text)
            _logger.info("[opf] %d entities: %s", len(opf_entities),
                         [(e.entity_type, repr(e.text)) for e in opf_entities])
            entities.extend(opf_entities)

        # GLiNER-based detection (zero-shot labels tuned for PII)
        if self.detector_backend == "gliner":
            gliner_entities = self._detect_with_gliner(text)
            _logger.info("[gliner] %d entities: %s", len(gliner_entities),
                         [(e.entity_type, repr(e.text)) for e in gliner_entities])
            entities.extend(gliner_entities)

        # Nemotron fine-tune on OPF architecture
        if self.detector_backend == "nemotron":
            nemotron_entities = self._detect_with_nemotron(text)
            _logger.info("[nemotron] %d entities: %s", len(nemotron_entities),
                         [(e.entity_type, repr(e.text)) for e in nemotron_entities])
            entities.extend(nemotron_entities)

        # Transformer-based detection (optional, heavyweight)
        if self.detector_backend in ("transformers", "hybrid"):
            transformer_entities = self._detect_with_transformers(text, detected_language)
            _logger.info("[transformers] %d entities: %s", len(transformer_entities),
                         [(e.entity_type, repr(e.text)) for e in transformer_entities])
            entities.extend(transformer_entities)
        elif self.detector_backend == "presidio":
            # Presidio/spaCy handles general NER (PERSON/ORG/LOC) but has no
            # vocabulary for specialized domains such as biomedical entities
            # (DIAGNOSIS, DRUG, LAB_VALUE, …).  When the active profile explicitly
            # requires those entity types, run the corresponding transformer models
            # on top of Presidio so cross-domain PII (e.g. medical data inside a
            # finance document) is still detected and anonymized.
            from .transformers_ner.models import get_required_model_domains
            required = get_required_model_domains(self.profile.dispositions)
            if required:
                _logger.info("[presidio+transformers] profile requires specialized domains %s — running transformer engines", sorted(required))
                transformer_entities = self._detect_with_transformers(text, detected_language)
                _logger.info("[transformers] %d entities: %s", len(transformer_entities),
                             [(e.entity_type, repr(e.text)) for e in transformer_entities])
                entities.extend(transformer_entities)
            else:
                _logger.info("[presidio+transformers] no specialized domains needed — skipping transformer models")

        # Step 4: Trim entity boundaries
        entities = self._trim_entity_boundaries(entities, text, detected_language)

        # Step 5: Deduplicate overlapping entities (BEFORE merge)
        before_dedup = len(entities)
        entities = self._dedupe_entities(entities)
        _logger.info("[dedup] %d -> %d entities", before_dedup, len(entities))

        # Step 6: Merge adjacent PERSON entities
        entities = self._merge_adjacent_persons(entities, text, detected_language)

        # Step 7: Apply linguistic filtering
        if self.profile.linguistic_filter_enabled:
            before_filter = len(entities)
            entities = self._apply_linguistic_filter(entities, text, detected_language)
            _logger.info("[linguistic_filter] %d -> %d entities", before_filter, len(entities))

        # Step 8: Filter by profile (only keep entities the profile cares about)
        before_profile = len(entities)
        entities = self._filter_by_profile(entities)
        _logger.info("[profile_filter] %d -> %d entities (final): %s",
                     before_profile, len(entities),
                     [(e.entity_type, repr(e.text), round(e.confidence, 3)) for e in entities])
        
        return entities, detected_language
    
    def _detect_language(self, text: str, language: str | None, thread_id: str | None) -> str:
        """Detect or retrieve cached language."""
        if language is not None:
            return language
        
        # Check cache first
        if thread_id and self.language_cache:
            cached = self.language_cache.get(thread_id)
            if cached:
                return cached
        
        # Detect language
        detected = self.language_detector.detect(text)
        
        # Cache for thread
        if thread_id and self.language_cache:
            self.language_cache.set(thread_id, detected)
        
        return detected
    
    def _detect_with_patterns(self, text: str, locale: str) -> list[Entity]:
        """Detect entities using pattern catalog."""
        entities = []
        
        # Get all patterns for locale (includes GLOBAL)
        patterns = self.pattern_catalog.get_all_patterns_for_locale(locale)
        
        for pattern in patterns:
            matches = pattern.match(text)
            for matched_text, start, end in matches:
                entities.append(Entity(
                    text=matched_text,
                    entity_type=pattern.entity_type,
                    start=start,
                    end=end,
                    confidence=pattern.confidence,
                    source=f"pattern:{locale}",
                ))
        
        return entities
    
    def _trim_entity_boundaries(self, entities: list[Entity], text: str, language: str) -> list[Entity]:
        """Trim common non-entity words from entity boundaries using NLP.
        
        Uses POS tagging to identify function words (verbs, adverbs, prepositions)
        that should not be part of entities. Language-agnostic approach - no keywords.
        
        spaCy sometimes includes contextual words in entity spans.
        This post-processing step removes them using linguistic analysis.
        
        Args:
            entities: List of detected entities
            text: Original text
        
        Returns:
            Entities with trimmed boundaries
        """
        trimmed = []
        
        # Use the filter for the detected language only.
        linguistic_filter = self._linguistic_filters.get(language)
        
        for entity in entities:
            # Only trim PERSON entities (others are regex-based and precise)
            if entity.entity_type != "PERSON":
                trimmed.append(entity)
                continue
            
            start = entity.start
            end = entity.end
            
            # Use linguistic trimming if available
            if linguistic_filter and hasattr(linguistic_filter.nlp_engine, 'trim_non_name_tokens'):
                try:
                    new_start, new_end = linguistic_filter.nlp_engine.trim_non_name_tokens(
                        text, start, end
                    )
                    if new_start < new_end:  # Valid trim
                        start, end = new_start, new_end
                except Exception:
                    # Fall back to no trimming if linguistic analysis fails
                    pass
            
            # Skip if entity became empty
            if start >= end:
                continue
            
            # Create trimmed entity
            trimmed_entity = Entity(
                text=text[start:end],
                entity_type=entity.entity_type,
                start=start,
                end=end,
                confidence=entity.confidence,
                source=entity.source,
            )
            trimmed.append(trimmed_entity)
        
        return trimmed
    
    def _merge_adjacent_persons(self, entities: list[Entity], text: str, language: str) -> list[Entity]:
        """Merge adjacent PERSON entities that are likely parts of the same name.
        
        Uses POS tagging to detect separators vs connectors (no hardcoded keywords).
        
        Example: "Ana" and "Garcia" separated by "is" → "Ana Garcia"
        Example: "Ana García" and "Ana García" separated by "con" → DON'T merge
        
        This handles cases where spaCy splits a full name into separate entities.
        Only merges if gap is a valid name connector (articles/determiners).
        
        Args:
            entities: List of detected entities
            text: Original text
        
        Returns:
            Entities with adjacent PERSON entities merged
        """
        if not entities:
            return entities
        
        # Get linguistic filter for POS analysis
        linguistic_filter = self._linguistic_filters.get(language)
        spacy_nlp = None
        if linguistic_filter is not None and hasattr(linguistic_filter, 'nlp_engine'):
            if hasattr(linguistic_filter.nlp_engine, '_nlp'):
                spacy_nlp = linguistic_filter.nlp_engine._nlp
        
        # Sort by start position for sequential processing
        sorted_entities = sorted(entities, key=lambda e: e.start)
        merged = []
        i = 0
        
        while i < len(sorted_entities):
            current = sorted_entities[i]
            
            # Non-PERSON entities pass through unchanged
            if current.entity_type != "PERSON":
                merged.append(current)
                i += 1
                continue
            
            # Look ahead for adjacent PERSON entities
            j = i + 1
            while j < len(sorted_entities):
                next_entity = sorted_entities[j]
                
                # Stop if next entity is not a PERSON
                if next_entity.entity_type != "PERSON":
                    break
                
                # Check gap between current end and next start
                gap = text[current.end:next_entity.start]
                gap_stripped = gap.strip()
                
                # Don't merge if gap is empty or too large
                if not gap_stripped or len(gap_stripped) > 10:
                    break
                
                # Use POS tagging to determine if gap is a separator
                should_merge = False
                
                if spacy_nlp:
                    try:
                        gap_doc = spacy_nlp(gap_stripped)
                        gap_tokens = list(gap_doc)
                        
                        if gap_tokens:
                            # Separators: prepositions, conjunctions (separate entities)
                            # Examples: "con" (ADP), "y" (CCONJ), "o" (CCONJ)
                            separators = {"ADP", "CONJ", "CCONJ", "SCONJ"}
                            has_separator = any(t.pos_ in separators for t in gap_tokens)
                            
                            if has_separator:
                                # Gap contains separator → don't merge
                                break
                            
                            # Connectors: articles, determiners (might be part of name)
                            # Examples: "de" in compound surnames could be DET
                            # But be conservative - only merge if ALL tokens are DET
                            connectors = {"DET"}
                            all_connectors = all(t.pos_ in connectors for t in gap_tokens)
                            
                            if all_connectors:
                                should_merge = True
                            else:
                                # Gap has other words → don't merge
                                break
                        else:
                            # Empty gap after parsing → merge
                            should_merge = True
                    except Exception:
                        # POS analysis failed, use fallback
                        # Only merge if gap is very short (< 3 chars, like space or "-")
                        if len(gap_stripped) < 3:
                            should_merge = True
                        else:
                            break
                else:
                    # No spaCy available, use conservative fallback
                    # Only merge if gap is very short (< 3 chars)
                    if len(gap_stripped) < 3:
                        should_merge = True
                    else:
                        break
                
                if not should_merge:
                    break
                
                # Merge: extend current entity to include next entity
                current = Entity(
                    text=text[current.start:next_entity.end],
                    entity_type="PERSON",
                    start=current.start,
                    end=next_entity.end,
                    confidence=max(current.confidence, next_entity.confidence),
                    source=current.source if current.confidence >= next_entity.confidence else next_entity.source,
                )
                j += 1
            
            merged.append(current)
            i = j if j > i + 1 else i + 1
        
        return merged

    
    def _detect_with_presidio(self, text: str, language: str, context_words: list[str] | None) -> list[Entity]:
        """Detect entities using Presidio for the specified language."""
        # Get or create Presidio engine for this language
        if language not in self._presidio_engines:
            self._presidio_engines[language] = self._init_presidio_engine(language)
        
        engine = self._presidio_engines[language]
        
        # Get entity types to detect from profile
        entity_types = list(self.profile.dispositions.keys()) if self.profile.dispositions else None

        # Avoid requesting unsupported entities from Presidio recognizer registry.
        if entity_types:
            try:
                supported = set(engine.list_supported_entities())
                filtered = [e for e in entity_types if e in supported]
                entity_types = filtered or None
            except Exception:
                # Fallback to original behavior if introspection is unavailable.
                pass
        
        # Build context from profile + user-provided
        all_context = list(context_words) if context_words else []
        
        # Analyze
        entities = engine.analyze(
            text=text,
            language=language,
            context=all_context if all_context else None,
            entities=entity_types,
        )
        
        return entities
    
    def _detect_with_transformers(self, text: str, language: str) -> list[Entity]:
        """Detect entities using all transformer engines required by the profile.

        One engine is loaded per model domain whose vocabulary is needed by the
        profile's dispositions (see models.get_required_model_domains). Running
        multiple engines lets each profile cover cross-domain leakage:
          - Finance: FinBERT for financial entities + biomedical NER for medical
          - Healthcare: biomedical NER (primary) + general NER baseline
          - Generic: all domains so nothing is missed
        """
        if language not in self._transformer_engines:
            self._transformer_engines[language] = self._init_transformer_engines(language)

        entities: list[Entity] = []
        for engine in self._transformer_engines[language]:
            entities.extend(engine.analyze(text))
        return entities

    def _detect_with_opf(self, text: str) -> list[Entity]:
        """Detect entities using OpenAI Privacy Filter.

        OPF returns span labels from its own taxonomy. We map those labels
        to this project's internal entity taxonomy so the existing profile,
        resolver, and anonymization logic can be reused unchanged.
        """
        if self._opf_engine is None:
            self._opf_engine = self._init_opf_engine()

        result = self._opf_engine.redact(text)
        entities: list[Entity] = []

        for span in result.detected_spans:
            mapped_type = self._map_opf_label(span.label)
            if mapped_type is None:
                continue

            entities.append(
                Entity(
                    text=span.text,
                    entity_type=mapped_type,
                    start=span.start,
                    end=span.end,
                    confidence=0.92,
                    source="opf",
                )
            )

        return entities

    def _detect_with_gliner(self, text: str) -> list[Entity]:
        """Detect entities using knowledgator GLiNER PII model."""
        if self._gliner_engine is None:
            self._gliner_engine = self._init_gliner_engine()

        predictions = self._gliner_engine.predict_entities(
            text,
            list(GLINER_LABEL_TO_ENTITY.keys()),
            threshold=0.3,
        )

        entities: list[Entity] = []
        for prediction in predictions:
            label = str(prediction.get("label", "")).strip().lower()
            mapped_type = self._map_gliner_label(label)
            if mapped_type is None:
                continue

            start = int(prediction.get("start", -1))
            end = int(prediction.get("end", -1))
            if start < 0 or end <= start or end > len(text):
                continue

            entities.append(
                Entity(
                    text=text[start:end],
                    entity_type=mapped_type,
                    start=start,
                    end=end,
                    confidence=float(prediction.get("score", 0.75)),
                    source="gliner",
                )
            )

        return entities

    def _detect_with_nemotron(self, text: str) -> list[Entity]:
        """Detect entities using OpenMed/privacy-filter-nemotron checkpoint."""
        if self._nemotron_engine is None:
            self._nemotron_engine = self._init_nemotron_engine()

        result = self._nemotron_engine.redact(text)
        entities: list[Entity] = []

        for span in result.detected_spans:
            mapped_type = self._map_nemotron_label(span.label)
            if mapped_type is None:
                continue

            entities.append(
                Entity(
                    text=span.text,
                    entity_type=mapped_type,
                    start=span.start,
                    end=span.end,
                    confidence=0.92,
                    source="nemotron",
                )
            )

        return entities

    @staticmethod
    def _map_opf_label(label: str) -> str | None:
        """Map OPF labels to canonical entity types."""
        label_norm = label.strip().lower()
        mapping: dict[str, str] = {
            "private_person":  ET.PERSON,
            "private_email":   ET.EMAIL,
            "private_phone":   ET.PHONE_NUMBER,
            "private_date":    ET.DATE_TIME,
            "private_address": ET.ADDRESS,
            "private_url":     ET.URL,
            "account_number":  ET.ACCOUNT_NUMBER,
            "secret":          ET.SECRET,
        }
        return mapping.get(label_norm)

    @staticmethod
    def _map_gliner_label(label: str) -> str | None:
        """Map GLiNER labels to internal entity types."""
        return GLINER_LABEL_TO_ENTITY.get(label)

    @staticmethod
    def _map_nemotron_label(label: str) -> str | None:
        """Map Nemotron (OPF-compatible) labels to canonical entity types."""
        label_norm = label.strip().lower()
        mapping: dict[str, str] = {
            # OPF-compatible coarse labels
            "private_person":  ET.PERSON,
            "private_email":   ET.EMAIL,
            "private_phone":   ET.PHONE_NUMBER,
            "private_date":    ET.DATE_TIME,
            "private_address": ET.ADDRESS,
            "private_url":     ET.URL,
            "account_number":  ET.ACCOUNT_NUMBER,
            "secret":          ET.SECRET,
            # Nemotron fine-grained labels
            "first_name":                     ET.PERSON,
            "last_name":                      ET.PERSON,
            "user_name":                      ET.SECRET,
            "email":                          ET.EMAIL,
            "phone_number":                   ET.PHONE_NUMBER,
            "fax_number":                     ET.PHONE_NUMBER,
            "url":                            ET.URL,
            "street_address":                 ET.ADDRESS,
            "city":                           ET.LOCATION,
            "county":                         ET.LOCATION,
            "state":                          ET.LOCATION,
            "country":                        ET.LOCATION,
            "postcode":                       ET.POSTAL_CODE,
            "date":                           ET.DATE_TIME,
            "date_of_birth":                  ET.DATE_TIME,
            "date_time":                      ET.DATE_TIME,
            "time":                           ET.DATE_TIME,
            "ssn":                            ET.SSN,
            "national_id":                    ET.NATIONAL_ID,
            "tax_id":                         ET.TAX_ID,
            "credit_debit_card":              ET.CREDIT_CARD,
            "bank_routing_number":            ET.ACCOUNT_NUMBER,
            "swift_bic":                      ET.ACCOUNT_NUMBER,
            "cvv":                            ET.SECRET,
            "pin":                            ET.SECRET,
            "password":                       ET.SECRET,
            "medical_record_number":          ET.MEDICAL_RECORD,
            "health_plan_beneficiary_number": ET.MEDICAL_RECORD,
            "customer_id":                    ET.NATIONAL_ID,
            "employee_id":                    ET.NATIONAL_ID,
            "unique_id":                      ET.NATIONAL_ID,
            "certificate_license_number":     ET.NATIONAL_ID,
            "license_plate":                  ET.LICENSE_PLATE,
            "vehicle_identifier":             ET.NATIONAL_ID,
            "ipv4":                           ET.IP_ADDRESS,
            "ipv6":                           ET.IP_ADDRESS,
            "mac_address":                    ET.IP_ADDRESS,
            "device_identifier":              ET.NATIONAL_ID,
            "api_key":                        ET.SECRET,
            "http_cookie":                    ET.SECRET,
        }
        return mapping.get(label_norm)
    
    def _get_entity_specificity(self, entity_type: str) -> int:
        """Get specificity rank for entity type (higher = more specific).
        
        Hierarchy (language-agnostic):
        1. Pattern-based identifiers (PHONE, EMAIL, SSN, etc.) - very precise
        2. IDs and numbers (DNI, MEDICAL_RECORD, CREDIT_CARD, etc.)
        3. Dates and times (DATE_TIME, DATE)
        4. Names (PERSON)
        5. Locations (LOCATION, ADDRESS)
        6. Generic catch-all
        
        Rationale:
        - Pattern recognizers (regex) are highly precise despite low confidence scores
        - NER models (spaCy) can mis-tag - e.g., "teléfono +34..." as PERSON
        - When overlap occurs, prefer specific > generic
        
        Args:
            entity_type: Entity type string
        
        Returns:
            Specificity rank (higher = more specific, prefer in conflicts)
        """
        # Tier 1: High-precision pattern matches (100 points base)
        if entity_type in {
            ET.PHONE_NUMBER, ET.EMAIL,
            ET.SSN, ET.IBAN, ET.CREDIT_CARD, ET.IP_ADDRESS, ET.URL, ET.SECRET,
        }:
            return 100
        
        # Tier 2: National IDs and financial/medical records (80 points)
        if entity_type in {
            ET.NATIONAL_ID, ET.MEDICAL_RECORD, ET.PASSPORT, ET.DRIVERS_LICENSE,
            ET.TAX_ID, ET.ACCOUNT_NUMBER,
        }:
            return 80
        
        # Tier 3: Dates and times (60 points)
        if entity_type in {ET.DATE_TIME, ET.DATE}:
            return 60
        
        # Tier 4: Person names (40 points)
        # Lower priority because NER can mis-tag non-person text as PERSON
        if entity_type == ET.PERSON:
            return 40
        
        # Tier 5: Locations (30 points)
        if entity_type in {ET.LOCATION, ET.ADDRESS, ET.POSTAL_CODE}:
            return 30
        
        # Tier 6: Everything else (10 points)
        return 10
    
    def _dedupe_entities(self, entities: list[Entity]) -> list[Entity]:
        """Remove duplicate and overlapping entities using specificity hierarchy.
        
        Strategy:
        - For same span: keep highest confidence
        - For overlaps: prefer more specific entity type (PHONE > PERSON)
        - Tie-breaker: longer entity, then higher confidence
        
        This prevents generic NER tags (PERSON) from shadowing precise patterns (PHONE_NUMBER).
        
        Args:
            entities: List of detected entities
        
        Returns:
            Deduplicated list with overlaps resolved by specificity
        """
        if not entities:
            return []
        
        # Sort by start position for sequential processing
        sorted_entities = sorted(entities, key=lambda e: e.start)
        
        deduped = []
        for entity in sorted_entities:
            # Check for overlap with already accepted entities
            should_add = True
            remove_existing = []
            
            for i, existing in enumerate(deduped):
                # Check if they overlap
                if entity.end <= existing.start or entity.start >= existing.end:
                    continue  # No overlap
                
                # Overlap detected - use specificity hierarchy to decide
                entity_spec = self._get_entity_specificity(entity.entity_type)
                existing_spec = self._get_entity_specificity(existing.entity_type)
                
                if entity_spec > existing_spec:
                    # Entity is more specific - remove existing, add entity
                    remove_existing.append(i)
                elif entity_spec < existing_spec:
                    # Existing is more specific - keep existing, skip entity
                    should_add = False
                    break
                else:
                    # Same specificity - tie-breakers
                    entity_len = entity.end - entity.start
                    existing_len = existing.end - existing.start
                    
                    if entity_len > existing_len:
                        # Entity is longer - remove existing
                        remove_existing.append(i)
                    elif entity_len < existing_len:
                        # Existing is longer - skip entity
                        should_add = False
                        break
                    else:
                        # Same length - use confidence
                        if entity.confidence > existing.confidence:
                            remove_existing.append(i)
                        else:
                            should_add = False
                            break
            
            # Remove shadowed entities
            for i in reversed(remove_existing):
                deduped.pop(i)
            
            # Add entity if it won all comparisons
            if should_add:
                deduped.append(entity)
        
        # Sort back to original order
        return sorted(deduped, key=lambda e: e.start)
    
    def _apply_linguistic_filter(self, entities: list[Entity], text: str, language: str) -> list[Entity]:
        """Apply NLP-based false positive filtering."""
        linguistic_filter = self._ensure_linguistic_filter(language)
        if linguistic_filter is None:
            return entities  # Filter creation failed
        
        return linguistic_filter.filter_entities(entities, text)

    def _ensure_linguistic_filter(self, language: str):
        """Get or create linguistic filter for language, if POS tagging is supported."""
        if not self.language_router.supports_pos_tagging(language):
            return None

        if language not in self._linguistic_filters:
            nlp = self.language_router.get_engine(language)
            from .linguistic_filter import create_linguistic_filter
            self._linguistic_filters[language] = create_linguistic_filter(nlp)

        return self._linguistic_filters[language]
    
    def _filter_by_profile(self, entities: list[Entity]) -> list[Entity]:
        """Filter entities based on profile dispositions.
        
        Only keep entities that:
        - Have a disposition defined in the profile
        - Meet the confidence threshold
        """
        filtered = []
        
        for entity in entities:
            disposition = self.profile.get_disposition(entity.entity_type)
            
            if disposition is None:
                # No disposition defined - skip (profile doesn't care about this entity)
                continue
            
            if not disposition.should_process(entity.confidence):
                # Below confidence threshold
                continue
            
            filtered.append(entity)
        
        return filtered
    
    def _init_presidio_engine(self, language: str):
        """Initialize Presidio analyzer engine for the specified language."""
        from .presidio_integration import PresidioAnalyzerEngine
        from .presidio_integration import PatternRecognizerFactory
        from .presidio_integration.custom_recognizers import create_enhanced_recognizers
        
        # Get spaCy model from router
        config = self.language_router.get_config(language)
        
        # Build custom recognizers list
        custom_recognizers = []
        
        # 1. Add enhanced recognizers (abbreviated names, dates, etc.)
        enhanced_recognizers = create_enhanced_recognizers(language)
        custom_recognizers.extend(enhanced_recognizers)
        
        # 2. Add pattern-based recognizers from our catalog for this language
        locale = self.language_router.get_patterns_locale(language)
        pattern_recognizers = PatternRecognizerFactory.from_catalog(
            self.pattern_catalog, 
            locale,
            language=language,
        )
        custom_recognizers.extend(pattern_recognizers)
        
        # Create language-specific Presidio engine
        # This will properly configure the registry for the target language
        engine = PresidioAnalyzerEngine(
            language=language,
            spacy_model=config.spacy_model,
            custom_recognizers=custom_recognizers,
        )
        
        return engine
    
    def _init_transformer_engines(self, language: str) -> list:
        """Initialize all transformer NER engines required by the profile.

        Loads one engine per specialized model domain derived from the profile's
        dispositions. Only entity types that are (a) regulated PII or GDPR
        Article 9 special-category data and (b) undetectable by regex patterns
        or the general CoNLL NER model trigger a specialized domain load.

        Currently the only specialized domain is "medical":
          - All profiles: biomedical NER (d4data/biomedical-ner-all, 265 MB)
            loaded whenever any medical entity type appears in dispositions
            (DIAGNOSIS, DRUG, PROCEDURE, SYMPTOM, LAB_VALUE, VITAL_SIGN, etc.)

        The general CoNLL transformer is only loaded when Presidio is NOT running,
        because spaCy already covers PERSON/LOCATION/ORG with equivalent accuracy.
        """
        import warnings
        from .transformers_ner import get_model_for_domain, DomainTransformerNEREngine
        from .transformers_ner.models import get_required_model_domains

        # Pinned model: honour the caller's explicit choice (testing / custom deployments).
        if self.transformer_model_id:
            return [DomainTransformerNEREngine(
                model_name=self.transformer_model_id,
                device=self.transformer_device,
                domain="general",
            )]

        # Derive specialized domains from profile dispositions (no profile coupling
        # inside models.py — the dict is passed directly).
        required_domains = get_required_model_domains(self.profile.dispositions)

        # In pure "presidio" mode spaCy is the sole NER backbone, so the general
        # CoNLL transformer would duplicate its output with ~420 MB of extra weight.
        # In "hybrid" mode the user explicitly requests maximum coverage; spaCy may
        # miss foreign-script or accented names (e.g. "Ana García" with en_core_web_sm),
        # so the general transformer runs as a complementary pass.  Dedup removes any
        # entity that both models agree on.
        if self.detector_backend != "presidio":
            required_domains.add("general")

        engines = []
        loaded_model_ids: set[str] = set()  # prevents loading the same weights twice

        for domain in sorted(required_domains):  # sorted for determinism
            try:
                model_config = get_model_for_domain(domain, language)
            except ValueError:
                warnings.warn(
                    f"No transformer model available for domain '{domain}' "
                    f"and language '{language}' — skipping.",
                    stacklevel=2,
                )
                continue

            model_name = model_config.model_id

            # CamemBERT tokenizer is currently incompatible in this runtime.
            # Use multilingual fallback for French general mode.
            if (
                domain == "general"
                and language == "fr"
                and sys.platform == "win32"
                and sys.version_info >= (3, 14)
                and model_name == "Jean-Baptiste/camembert-ner"
            ):
                model_name = "Davlan/xlm-roberta-base-ner-hrl"

            # Skip if this exact model is already in the engine list (e.g. financial and
            # legal both resolve to tner/roberta-large-ontonotes5). The first domain's
            # normalizer is used; since the financial normalizer already covers LAW→STATUTE
            # and ORG→LEGAL_ENTITY, no label is lost when legal is skipped this way.
            if model_name in loaded_model_ids:
                import logging as _log
                _log.getLogger(__name__).debug(
                    "Skipping domain '%s': model %r already loaded for another domain.",
                    domain,
                    model_name,
                )
                continue

            loaded_model_ids.add(model_name)
            engines.append(DomainTransformerNEREngine(
                model_name=model_name,
                device=self.transformer_device,
                domain=domain,
            ))

        return engines

    def _init_opf_engine(self):
        """Initialize OpenAI Privacy Filter runtime."""
        if sys.platform == "win32" and sys.version_info >= (3, 14):
            raise ImportError(
                "opf requires Python < 3.14 on Windows in this runtime "
                "(native backend instability detected)."
            )

        try:
            from opf._api import OPF  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "opf is not installed. Install with: "
                "pip install 'pii-firewall[opf]'"
            ) from exc

        # CPU default to keep compatibility across environments.
        # OPF supports local checkpoint caching and will auto-download once.
        kwargs = {
            "device": "cpu",
            "output_mode": "typed",
            "decode_mode": "viterbi",
        }

        if self.opf_checkpoint:
            for checkpoint_key in ("checkpoint", "model_name", "model_id"):
                try:
                    return OPF(**kwargs, **{checkpoint_key: self.opf_checkpoint})
                except TypeError:
                    continue

        return OPF(**kwargs)

    def _init_gliner_engine(self):
        """Initialize GLiNER PII model runtime."""
        try:
            from gliner import GLiNER  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "gliner is not installed. Install with: "
                "pip install 'pii-firewall[gliner]'"
            ) from exc

        return GLiNER.from_pretrained(self.gliner_model_id)

    def _init_nemotron_engine(self):
        """Initialize OpenMed Nemotron checkpoint through OPF runtime."""
        if sys.platform == "win32" and sys.version_info >= (3, 14):
            raise ImportError(
                "nemotron requires Python < 3.14 on Windows in this runtime "
                "(native backend instability detected)."
            )

        try:
            from opf._api import OPF  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "opf is not installed. Install with: "
                "pip install 'pii-firewall[opf]'"
            ) from exc

        base_kwargs = {
            "device": "cpu",
            "output_mode": "typed",
            "decode_mode": "viterbi",
        }
        checkpoint = "OpenMed/privacy-filter-nemotron"

        for checkpoint_key in ("checkpoint", "model_name", "model_id"):
            try:
                return OPF(**base_kwargs, **{checkpoint_key: checkpoint})
            except TypeError:
                continue

        return OPF(**base_kwargs)
