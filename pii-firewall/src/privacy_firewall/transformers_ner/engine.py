"""Transformer NER engine using HuggingFace models.

This is the foundation for transformer-based entity recognition.
Full implementation would use transformers.pipeline with NER models.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ..types import Entity
from .. import entity_types as ET

_logger = logging.getLogger(__name__)


@dataclass
class TransformerNEREngine:
    """NER engine using HuggingFace transformer models.
    
    Supports:
    - General NER models (dslim/bert-base-NER, xlm-roberta-large-finetuned-conll03)
    - Domain-specific models (BioBERT, FinBERT, LegalBERT)
    - Multilingual models (XLM-RoBERTa)
    
    Attributes:
        model_name: HuggingFace model identifier
        aggregation_strategy: How to aggregate subword tokens ("simple", "first", "average", "max")
        device: Device to run on (-1 for CPU, 0 for GPU)
        use_fast_tokenizer: Use fast Rust-based tokenizer
    """
    
    model_name: str
    aggregation_strategy: str = "simple"
    device: int = -1  # CPU by default
    use_fast_tokenizer: bool = True
    
    _pipeline: Any = field(default=None, init=False, repr=False)
    
    def __post_init__(self) -> None:
        """Initialize transformer pipeline (lazy loading)."""
        # Don't load model in __post_init__ - wait for first use
        pass
    
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
        """Detect entities in text using transformer model.

        At DEBUG log level this method emits two lines per call:
          1. Raw pipeline output (entity_group, score, word) before normalisation.
          2. Final Entity list after normalisation.
        This lets you quickly audit what each model actually recognises without
        touching production log levels.

        Args:
            text: Input text

        Returns:
            List of Entity objects
        """
        self._ensure_pipeline()

        results = self._pipeline(text)

        _logger.debug(
            "[%s] raw predictions (%d): %s",
            self.model_name,
            len(results),
            [(r["entity_group"], round(r["score"], 3), r["word"]) for r in results],
        )

        entities = []
        for item in results:
            raw_label = item["entity_group"]
            normalized = self._normalize_entity_type(raw_label)
            _logger.debug(
                "  label %r -> %r  score=%.3f  span=%d:%d  word=%r",
                raw_label,
                normalized,
                item["score"],
                item["start"],
                item["end"],
                item["word"],
            )
            entities.append(
                Entity(
                    text=item["word"],
                    entity_type=normalized,
                    start=item["start"],
                    end=item["end"],
                    confidence=float(item["score"]),
                    source=f"transformer:{self.model_name}",
                )
            )

        _logger.debug(
            "[%s] produced %d entities: %s",
            self.model_name,
            len(entities),
            [e.entity_type for e in entities],
        )
        return entities
    
    @staticmethod
    def _normalize_entity_type(entity_group: str) -> str:
        """Normalize generic transformer entity labels to canonical entity types."""
        mapping: dict[str, str] = {
            # CoNLL-2003 labels (dslim/bert-base-NER, xlm-roberta-base-ner-hrl, etc.)
            "PER":          ET.PERSON,
            "PERSON":       ET.PERSON,
            "ORG":          ET.COMPANY_NAME,
            "ORGANIZATION": ET.COMPANY_NAME,
            "LOC":          ET.LOCATION,
            "LOCATION":     ET.LOCATION,
            "GPE":          ET.LOCATION,
            # OntoNotes 5.0 labels (tner/roberta-large-ontonotes5 et al.)
            "DATE":         ET.DATE_TIME,
            "TIME":         ET.DATE_TIME,
            "MONEY":        ET.TRANSACTION_AMOUNT,
            "PERCENT":      ET.PERCENTAGE,
            "LAW":          ET.STATUTE,
            "FAC":          ET.LOCATION,
            "NORP":         ET.LOCATION,
            # Medical (BioBERT, BC5CDR, generic)
            "DISEASE":      ET.DIAGNOSIS,
            "CHEMICAL":     ET.DRUG,
            "DRUG":         ET.DRUG,
        }
        return mapping.get(entity_group.upper(), entity_group.upper())


@dataclass
class DomainTransformerNEREngine(TransformerNEREngine):
    """Transformer NER engine specialized for domain-specific models.
    
    This subclass handles domain-specific entity type mappings and
    post-processing for medical, financial, or legal domains.
    """
    
    domain: str = "general"  # "medical", "financial", "legal", "general"
    
    def _normalize_entity_type(self, entity_group: str) -> str:
        """Domain-aware entity type normalization."""
        if self.domain == "medical":
            return self._normalize_medical_entity(entity_group)
        elif self.domain == "financial":
            return self._normalize_financial_entity(entity_group)
        elif self.domain == "legal":
            return self._normalize_legal_entity(entity_group)
        else:
            return super()._normalize_entity_type(entity_group)
    
    @staticmethod
    def _normalize_medical_entity(entity_group: str) -> str:
        """Normalize medical entity labels to canonical types.

        Covers labels emitted by:
          - d4data/biomedical-ner-all  (aggregated BIO labels: "Disease_disorder" etc.)
          - samrawal/bert-base-uncased_clinical-ner  ("problem", "treatment", "test")
          - Generic biomedical models  (BC5CDR: "DISEASE", "CHEMICAL")
        """
        mapping: dict[str, str] = {
            # ── d4data/biomedical-ner-all ─────────────────────────────────────────
            # aggregation_strategy='simple' strips B-/I- and preserves casing;
            # after .upper() the keys below are the effective lookup strings.
            "DISEASE_DISORDER":      ET.DIAGNOSIS,
            "SIGN_SYMPTOM":          ET.SYMPTOM,
            "MEDICATION":            ET.DRUG,
            "DIAGNOSTIC_PROCEDURE":  ET.PROCEDURE,
            "THERAPEUTIC_PROCEDURE": ET.PROCEDURE,
            "LAB_VALUE":             ET.LAB_VALUE,
            "BIOLOGICAL_STRUCTURE":  ET.ANATOMICAL_SITE,
            "CLINICAL_EVENT":        ET.PROCEDURE,
            "FAMILY_HISTORY":        ET.DIAGNOSIS,
            "DOSAGE":                ET.DRUG,
            "HISTORY":               ET.DIAGNOSIS,
            "ACTIVITY":              ET.PROCEDURE,
            "OUTCOME":               ET.DIAGNOSIS,
            "SEVERITY":              ET.SYMPTOM,
            # ── samrawal/bert-base-uncased_clinical-ner ───────────────────────────
            "PROBLEM":   ET.DIAGNOSIS,
            "TREATMENT": ET.PROCEDURE,
            "TEST":      ET.LAB_VALUE,
            # ── Generic / BC5CDR / legacy labels ─────────────────────────────────
            "DISEASE":   ET.DIAGNOSIS,
            "DISORDER":  ET.DIAGNOSIS,
            "SYMPTOM":   ET.SYMPTOM,
            "CHEMICAL":  ET.DRUG,
            "DRUG":      ET.DRUG,
            "PROCEDURE": ET.PROCEDURE,
            "ANATOMY":   ET.ANATOMICAL_SITE,
            "GENE":      ET.DIAGNOSIS,   # gene name often indicates condition context
            "PROTEIN":   ET.DIAGNOSIS,
        }
        return mapping.get(entity_group.upper(), entity_group.upper())
    
    @staticmethod
    def _normalize_financial_entity(entity_group: str) -> str:
        """Normalize financial entity labels to canonical types.

        Covers labels emitted by:
          - tner/roberta-large-ontonotes5  (OntoNotes 5.0 label set)
        """
        mapping: dict[str, str] = {
            # OntoNotes 5.0 labels
            "MONEY":        ET.TRANSACTION_AMOUNT,
            "PERCENT":      ET.PERCENTAGE,
            "ORG":          ET.COMPANY_NAME,
            "ORGANIZATION": ET.COMPANY_NAME,
            "PERSON":       ET.PERSON,
            "PER":          ET.PERSON,
            "DATE":         ET.DATE_TIME,
            "TIME":         ET.DATE_TIME,
            "GPE":          ET.LOCATION,
            "LOC":          ET.LOCATION,
            "LOCATION":     ET.LOCATION,
            "FAC":          ET.LOCATION,
            "NORP":         ET.LOCATION,
            "LAW":          ET.STATUTE,
            # Legacy label kept for backwards compat
            "CURRENCY":     ET.CURRENCY,
        }
        return mapping.get(entity_group.upper(), entity_group.upper())
    
    @staticmethod
    def _normalize_legal_entity(entity_group: str) -> str:
        """Normalize legal entity labels to canonical types.

        Covers labels emitted by:
          - tner/roberta-large-ontonotes5  (OntoNotes 5.0 label set)
        """
        mapping: dict[str, str] = {
            # OntoNotes 5.0 labels
            "LAW":          ET.STATUTE,
            "ORG":          ET.LEGAL_ENTITY,    # courts, firms, agencies
            "ORGANIZATION": ET.LEGAL_ENTITY,
            "PERSON":       ET.PERSON,
            "PER":          ET.PERSON,
            "GPE":          ET.LOCATION,
            "LOC":          ET.LOCATION,
            "LOCATION":     ET.LOCATION,
            "DATE":         ET.DATE_TIME,
            # Legacy legal-bert labels (kept for backwards compat)
            "COURT":        ET.LEGAL_ENTITY,
            "JUDGE":        ET.PERSON,
            "LAWYER":       ET.PERSON,
            "CASE":         ET.CASE_NUMBER,
            "STATUTE":      ET.STATUTE,
        }
        return mapping.get(entity_group.upper(), entity_group.upper())
