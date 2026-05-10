"""Transformer NER engine using HuggingFace pipelines."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ..types import Entity
from .. import entity_types as ET

_logger = logging.getLogger(__name__)


@dataclass
class TransformerNEREngine:
    """NER engine backed by a HuggingFace token-classification pipeline.

    Supports general CoNLL NER models and domain-specific biomedical models.
    The pipeline is lazy-loaded on the first call to :meth:`analyze`.

    Attributes:
        model_name: HuggingFace model identifier.
        aggregation_strategy: Subword aggregation strategy passed to the
            pipeline (``"first"`` merges fragments using the first token's
            label — recommended for all current models).
        device: Torch device index (``-1`` = CPU, ``0`` = first GPU).
        use_fast_tokenizer: Use the Rust-backed fast tokenizer when available.
    """
    
    model_name: str
    aggregation_strategy: str = "first"  # merges subword tokens into word spans
    device: int = -1  # CPU by default
    use_fast_tokenizer: bool = True
    
    _pipeline: Any = field(default=None, init=False, repr=False)
    
    def __post_init__(self) -> None:
        pass  # pipeline is loaded lazily on first analyze() call
    
    def _ensure_pipeline(self) -> None:
        """Lazy load the NER pipeline."""
        if self._pipeline is not None:
            return
        
        try:
            from transformers import pipeline  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "transformers is not installed. "
                    "Install with: pip install 'pii-firewall[transformers]'"
            ) from exc
        
        _logger.info("Loading transformer model: %s", self.model_name)
        try:
            self._pipeline = pipeline(
                "ner",
                model=self.model_name,
                aggregation_strategy=self.aggregation_strategy,
                device=self.device,
                use_fast=self.use_fast_tokenizer,
            )
        except TypeError:
            # Some model/tokenizer combos can fail with fast tokenizers in newer Python runtimes.
            # Retry with the slow tokenizer to keep the backend operational.
            self._pipeline = pipeline(
                "ner",
                model=self.model_name,
                aggregation_strategy=self.aggregation_strategy,
                device=self.device,
                use_fast=False,
            )
        _logger.info("Transformer model loaded: %s", self.model_name)
    
    def analyze(self, text: str) -> list[Entity]:
        """Detect entities in text.

        At DEBUG log level emits raw pipeline predictions before normalisation
        and the final entity list, useful for auditing model behaviour.

        Args:
            text: Input text.

        Returns:
            List of :class:`~privacy_firewall.types.Entity` objects.
        """
        self._ensure_pipeline()

        _logger.info("[transformer:%s] analyzing %d chars: %r",
                     self.model_name, len(text),
                     text[:100] + ("..." if len(text) > 100 else ""))

        results = self._pipeline(text)

        _logger.info(
            "[transformer:%s] raw predictions (%d): %s",
            self.model_name,
            len(results),
            [(r["entity_group"], round(r["score"], 3), r["word"]) for r in results],
        )

        entities = []
        for item in results:
            raw_label = item["entity_group"]
            word = item["word"]
            score = float(item["score"])

            normalized = self._normalize_entity_type(raw_label)
            if not normalized:
                # Empty string = non-PII label (Time, Date, Severity, etc.) — skip
                _logger.info(
                    "  [transformer:%s] label %r -> DROPPED (non-PII)  score=%.3f  word=%r",
                    self.model_name, raw_label, score, word,
                )
                continue
            _logger.info(
                "  [transformer:%s] label %r -> %r  score=%.3f  word=%r",
                self.model_name, raw_label, normalized, score, word,
            )
            entities.append(
                Entity(
                    text=word.strip(),
                    entity_type=normalized,
                    start=item["start"],
                    end=item["end"],
                    confidence=score,
                    source=f"transformer:{self.model_name}",
                )
            )

        _logger.info(
            "[transformer:%s] => %d entities emitted: %s",
            self.model_name,
            len(entities),
            [(e.entity_type, repr(e.text)) for e in entities],
        )
        return entities
    
    @staticmethod
    def _normalize_entity_type(entity_group: str) -> str:
        """Map CoNLL-2003 labels to canonical entity type constants."""
        mapping: dict[str, str] = {
            # CoNLL-2003 (dslim/bert-base-NER, xlm-roberta-base-ner-hrl, etc.)
            "PER":          ET.PERSON,
            "PERSON":       ET.PERSON,
            "ORG":          ET.COMPANY_NAME,
            "ORGANIZATION": ET.COMPANY_NAME,
            "LOC":          ET.LOCATION,
            "LOCATION":     ET.LOCATION,
            "GPE":          ET.LOCATION,
        }
        return mapping.get(entity_group.upper(), entity_group.upper())


@dataclass
class DomainTransformerNEREngine(TransformerNEREngine):
    """Transformer NER engine with domain-specific label normalisation.

    Currently the only specialised domain is ``"medical"``, which maps
    biomedical label vocabularies (d4data, BC5CDR) to the
    canonical entity type constants.  The ``"general"`` domain falls back to
    the CoNLL label mapping in the base class.
    """

    domain: str = "general"  # "medical" | "general"

    def _normalize_entity_type(self, entity_group: str) -> str:
        """Dispatch to domain-specific normaliser."""
        if self.domain == "medical":
            return self._normalize_medical_entity(entity_group)
        return super()._normalize_entity_type(entity_group)
    
    @staticmethod
    def _normalize_medical_entity(entity_group: str) -> str:
        """Map biomedical label vocabularies to canonical entity type constants.

        Covers labels emitted by:
        - ``d4data/biomedical-ner-all`` — aggregated BIO labels such as
          ``Disease_disorder``, ``Sign_symptom``, ``Medication``, etc.
          After ``.upper()`` these become the dict keys below.
        - Generic BC5CDR labels: ``DISEASE``, ``CHEMICAL``.
        """
        # Labels that map to canonical PII/PHI entity types.
        mapping: dict[str, str] = {
            # d4data/biomedical-ner-all labels (uppercased after aggregation)
            "DISEASE_DISORDER":      ET.DIAGNOSIS,
            "SIGN_SYMPTOM":          ET.SYMPTOM,
            "MEDICATION":            ET.DRUG,
            "DIAGNOSTIC_PROCEDURE":  ET.PROCEDURE,
            "THERAPEUTIC_PROCEDURE": ET.PROCEDURE,
            "LAB_VALUE":             ET.LAB_VALUE,
            "BIOLOGICAL_STRUCTURE":  ET.ANATOMICAL_SITE,
            "FAMILY_HISTORY":        ET.DIAGNOSIS,
            "DOSAGE":                ET.DRUG,
            "HISTORY":               ET.DIAGNOSIS,
            # Generic / BC5CDR labels
            "DISEASE":   ET.DIAGNOSIS,
            "DISORDER":  ET.DIAGNOSIS,
            "SYMPTOM":   ET.SYMPTOM,
            "CHEMICAL":  ET.DRUG,
            "DRUG":      ET.DRUG,
            "PROCEDURE": ET.PROCEDURE,
            "ANATOMY":   ET.ANATOMICAL_SITE,
            "GENE":      ET.DIAGNOSIS,
            "PROTEIN":   ET.DIAGNOSIS,
        }
        # Labels that are NOT PII/PHI and must be dropped (return None).
        # These are clinical context labels that carry no identifying information.
        non_pii_labels = {
            "AGE",             # demographic — captured by regex AGE patterns instead
            "TIME",            # temporal expression — not an identifier
            "DATE",            # date fragment — not an identifier (regex handles dates)
            "SEVERITY",        # clinical severity adjective (e.g. 'severe') — not PII
            "CLINICAL_EVENT",  # generic clinical verb (e.g. 'came', 'visited') — not PII
            "ACTIVITY",        # patient activity — not PII
            "OUTCOME",         # clinical outcome — not a direct identifier
        }
        upper = entity_group.upper()
        if upper in non_pii_labels:
            return ""  # sentinel: caller must drop entities with empty type
        return mapping.get(upper, upper)
