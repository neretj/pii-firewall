"""Enhanced Presidio engine with full capabilities.

This module wraps Presidio's AnalyzerEngine and AnonymizerEngine with:
- Custom recognizer registration
- Context-aware analysis
- Domain-specific entity detection
- Per-entity operator configuration
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..types import Entity


@dataclass
class PresidioAnalyzerEngine:
    """Wrapper for Presidio AnalyzerEngine with custom recognizers.
    
    Exposes full Presidio capabilities:
    - Custom pattern recognizers
    - Context-aware detection
    - RecognizerRegistry management
    - Multi-language support
    """
    
    language: str = "en"
    spacy_model: str | None = None
    custom_recognizers: list[Any] = field(default_factory=list)
    supported_entities: list[str] | None = None  # None = all entities
    
    def __post_init__(self) -> None:
        """Initialize Presidio AnalyzerEngine for the specified language.
        
        Presidio's proper multi-language support requires:
        1. NLP engine configured for specific language
        2. RecognizerRegistry with language-appropriate recognizers
        3. AnalyzerEngine that accepts ONLY that language
        
        For English: use predefined recognizers (SSN, credit card, etc.)
        For other languages: use SpacyRecognizer for NER + custom patterns
        """
        try:
            from presidio_analyzer import AnalyzerEngine, RecognizerRegistry  # type: ignore
            from presidio_analyzer.nlp_engine import NlpEngineProvider  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "Presidio dependencies not installed. "
                 "Install with: pip install 'pii-firewall[presidio]'"
            ) from exc
        
        # Determine spaCy model for this language
        if self.spacy_model is None:
            self.spacy_model = self._get_default_model(self.language)
        
        # Configure NLP engine for this specific language
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": self.language, "model_name": self.spacy_model}
            ],
        }
        
        provider = NlpEngineProvider(nlp_configuration=nlp_config)
        nlp_engine = provider.create_engine()
        
        # Create recognizer registry for this language
        registry = RecognizerRegistry()
        
        if self.language == "en":
            # English: load all predefined recognizers
            # This includes SSN, credit card, email, phone, SpacyRecognizer, etc.
            registry.load_predefined_recognizers(
                nlp_engine=nlp_engine,
                languages=["en"],
            )
        else:
            # Non-English: manually create SpacyRecognizer for this language
            # We DON'T use load_predefined_recognizers() because it loads
            # English-only recognizers (SSN, credit card, etc.) which causes
            # registry.supported_languages to be ['en'], creating mismatch errors
            
            # Import here to avoid circular dependency
            from presidio_analyzer.predefined_recognizers import SpacyRecognizer
            
            spacy_recognizer = SpacyRecognizer(
                supported_language=self.language,
                supported_entities=["PERSON", "LOCATION", "ORGANIZATION", "NRP", "DATE_TIME"],
            )
            registry.add_recognizer(spacy_recognizer)
        
        # Add custom recognizers (pattern-based from our catalog)
        for recognizer in self.custom_recognizers:
            # Filter recognizers by language support
            if hasattr(recognizer, 'supported_language'):
                if recognizer.supported_language == self.language:
                    registry.add_recognizer(recognizer)
            elif hasattr(recognizer, 'supported_languages'):
                if self.language in recognizer.supported_languages:
                    registry.add_recognizer(recognizer)
            else:
                # No language info - assume universal (like pattern recognizers)
                registry.add_recognizer(recognizer)
        
        # Create analyzer engine for this language
        # For non-English, we don't specify supported_languages to avoid
        # mismatch with registry's default ['en']. The engine will use
        # the recognizers' languages to determine what it supports.
        if self.language == "en":
            self._engine = AnalyzerEngine(
                nlp_engine=nlp_engine,
                registry=registry,
                supported_languages=["en"],
            )
        else:
            # Don't specify supported_languages - let it be inferred from recognizers
            self._engine = AnalyzerEngine(
                nlp_engine=nlp_engine,
                registry=registry,
            )
    
    def analyze(
        self,
        text: str,
        language: str | None = None,
        context: list[str] | None = None,
        entities: list[str] | None = None,
        score_threshold: float = 0.5,
    ) -> list[Entity]:
        """Analyze text for PII entities.
        
        Args:
            text: Text to analyze
            language: Language code (defaults to engine language)
            context: Context words to boost detection (e.g., ["patient", "diagnosis"])
            entities: Specific entity types to detect (None = all)
            score_threshold: Minimum confidence score (default: 0.5 for better recall)
        
        Returns:
            List of detected entities
        """
        lang = language or self.language
        
        # Use supported_entities if entities not specified
        entity_list = entities or self.supported_entities
        
        # Analyze with Presidio
        results = self._engine.analyze(
            text=text,
            language=lang,
            context=context,
            entities=entity_list,
            score_threshold=score_threshold,
        )
        
        # Convert to our Entity format
        entities_out = [
            Entity(
                text=text[item.start : item.end],
                entity_type=item.entity_type,
                start=item.start,
                end=item.end,
                confidence=float(item.score),
                source="presidio",
            )
            for item in results
        ]
        
        return entities_out
    
    def add_recognizer(self, recognizer: Any) -> None:
        """Add a custom recognizer to the engine's registry."""
        self._engine.registry.add_recognizer(recognizer)
    
    def remove_recognizer(self, recognizer_name: str) -> None:
        """Remove a recognizer from the registry."""
        self._engine.registry.remove_recognizer(recognizer_name)
    
    def list_recognizers(self) -> list[str]:
        """List all registered recognizer names."""
        return [r.name for r in self._engine.registry.recognizers]

    def list_supported_entities(self) -> list[str]:
        """List unique entity types currently supported by recognizers."""
        supported: set[str] = set()
        for recognizer in self._engine.registry.recognizers:
            entities = getattr(recognizer, "supported_entities", None)
            if entities:
                supported.update(str(e) for e in entities)
        return sorted(supported)
    
    @staticmethod
    def _get_default_model(language: str) -> str:
        """Get default spaCy model for language."""
        models = {
            "es": "es_core_news_sm",
            "en": "en_core_web_sm",
            "fr": "fr_core_news_sm",
            "de": "de_core_news_sm",
            "it": "it_core_news_sm",
            "pt": "pt_core_news_sm",
        }
        return models.get(language, "xx_ent_wiki_sm")


@dataclass
class PresidioAnonymizerEngine:
    """Wrapper for Presidio AnonymizerEngine with per-entity operators.
    
    This enables:
    - Different anonymization strategies per entity type
    - Presidio's built-in operators (replace, redact, hash, mask, encrypt)
    - Custom operators
    - Deanonymization (reversible pseudo-anonymization)
    """
    
    def __post_init__(self) -> None:
        try:
            from presidio_anonymizer import AnonymizerEngine, DeanonymizerEngine  # type: ignore
            from presidio_anonymizer.entities import OperatorConfig  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "presidio-anonymizer not installed. "
                 "Install with: pip install 'pii-firewall[presidio]'"
            ) from exc
        
        self._AnonymizerEngine = AnonymizerEngine
        self._DeanonymizerEngine = DeanonymizerEngine
        self._OperatorConfig = OperatorConfig
        
        self._anonymizer = self._AnonymizerEngine()
        self._deanonymizer = self._DeanonymizerEngine()
    
    def anonymize(
        self,
        text: str,
        analyzer_results: list,
        operators: dict[str, Any] | None = None,
    ) -> tuple[str, list[dict]]:
        """Anonymize text using presidio operators.
        
        Args:
            text: Original text
            analyzer_results: Results from PresidioAnalyzerEngine
            operators: Map of entity_type → OperatorConfig
        
        Returns:
            (anonymized_text, mapping for deanonymization)
        """
        result = self._anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results,
            operators=operators,
        )
        
        # Extract mapping for reversibility
        mapping = []
        for item in result.items:
            mapping.append({
                "entity_type": item.entity_type,
                "start": item.start,
                "end": item.end,
                "operator": item.operator,
                "text": item.text,
            })
        
        return result.text, mapping
    
    def deanonymize(
        self,
        text: str,
        mapping: list[dict],
    ) -> str:
        """Reverse anonymization (for pseudonymized entities).
        
        Args:
            text: Anonymized text
            mapping: Mapping from anonymize() call
        
        Returns:
            Original text with entities restored
        """
        # Convert mapping to deanonymizer format
        deanonymizer_mapping = {}
        for item in mapping:
            if item["text"] not in deanonymizer_mapping:
                deanonymizer_mapping[item["text"]] = item["operator"]
        
        result = self._deanonymizer.deanonymize(
            text=text,
            entities=deanonymizer_mapping,
        )
        
        return result.text
    
    def create_operator_config(
        self,
        operator_name: str,
        params: dict | None = None,
    ) -> Any:
        """Create an OperatorConfig for use with anonymize().
        
        Built-in operators:
        - "replace": Replace with new value
        - "redact": Replace with empty string or placeholder
        - "hash": SHA256 hash
        - "mask": Partial masking (e.g., ****5678)
        - "encrypt": AES encryption (reversible)
        - "keep": No-op
        
        Example:
            config = engine.create_operator_config("mask", {"chars_to_mask": 12, "masking_char": "*"})
        """
        return self._OperatorConfig(operator_name, params or {})
