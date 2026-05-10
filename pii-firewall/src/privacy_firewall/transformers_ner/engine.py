"""Transformer NER engine using HuggingFace models.

This is the foundation for transformer-based entity recognition.
Full implementation would use transformers.pipeline with NER models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..types import Entity
from .. import entity_types as ET


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
        
        print(f"Loading transformer model: {self.model_name}...")
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
        print(f"✓ Model loaded: {self.model_name}")
    
    def analyze(self, text: str) -> list[Entity]:
        """Detect entities in text using transformer model.
        
        Args:
            text: Input text
        
        Returns:
            List of Entity objects
        """
        self._ensure_pipeline()
        
        # Run NER
        results = self._pipeline(text)
        
        # Convert to Entity format
        entities = []
        for item in results:
            # Transformer NER returns:
            # - entity_group: entity type (PERSON, ORG, LOC, etc.)
            # - score: confidence
            # - start/end: character offsets
            # - word: matched text
            
            entities.append(
                Entity(
                    text=item["word"],
                    entity_type=self._normalize_entity_type(item["entity_group"]),
                    start=item["start"],
                    end=item["end"],
                    confidence=float(item["score"]),
                    source=f"transformer:{self.model_name}",
                )
            )
        
        return entities
    
    @staticmethod
    def _normalize_entity_type(entity_group: str) -> str:
        """Normalize generic transformer entity labels to canonical entity types."""
        mapping: dict[str, str] = {
            # CoNLL-style labels
            "PER":          ET.PERSON,
            "PERSON":       ET.PERSON,
            "ORG":          ET.COMPANY_NAME,
            "ORGANIZATION": ET.COMPANY_NAME,
            "LOC":          ET.LOCATION,
            "LOCATION":     ET.LOCATION,
            "GPE":          ET.LOCATION,
            # OntoNotes labels
            "DATE":         ET.DATE_TIME,
            "TIME":         ET.DATE_TIME,
            "MONEY":        ET.TRANSACTION_AMOUNT,
            "PERCENT":      ET.PERCENTAGE,
            "CARDINAL":     ET.TRANSACTION_AMOUNT,
            # Medical (BioBERT)
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
        """Normalize medical entity labels to canonical types."""
        mapping: dict[str, str] = {
            "DISEASE":   ET.DIAGNOSIS,
            "DISORDER":  ET.DIAGNOSIS,
            "SYMPTOM":   ET.SYMPTOM,
            "CHEMICAL":  ET.DRUG,
            "DRUG":      ET.DRUG,
            "PROCEDURE": ET.PROCEDURE,
            "TEST":      ET.LAB_VALUE,
            "ANATOMY":   ET.ANATOMICAL_SITE,
        }
        return mapping.get(entity_group.upper(), entity_group.upper())
    
    @staticmethod
    def _normalize_financial_entity(entity_group: str) -> str:
        """Normalize financial entity labels to canonical types."""
        mapping: dict[str, str] = {
            "MONEY":        ET.TRANSACTION_AMOUNT,
            "CURRENCY":     ET.CURRENCY,
            "ORG":          ET.COMPANY_NAME,
            "ORGANIZATION": ET.COMPANY_NAME,
            "PERCENT":      ET.PERCENTAGE,
            "DATE":         ET.DATE_TIME,
        }
        return mapping.get(entity_group.upper(), entity_group.upper())
    
    @staticmethod
    def _normalize_legal_entity(entity_group: str) -> str:
        """Normalize legal entity labels to canonical types."""
        mapping: dict[str, str] = {
            "COURT":  ET.LEGAL_ENTITY,
            "JUDGE":  ET.PERSON,
            "LAWYER": ET.PERSON,
            "CASE":   ET.CASE_NUMBER,
            "STATUTE": ET.STATUTE,
            "ORG":    ET.COMPANY_NAME,
            "LAW":    ET.STATUTE,
        }
        return mapping.get(entity_group.upper(), entity_group.upper())
