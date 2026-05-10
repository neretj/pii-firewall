"""Transformer-based NER backend (HuggingFace).

This module provides infrastructure for using transformer models as an alternative
to spaCy for NER. Key benefits:
- Better accuracy for non-English languages
- Domain-specific models (BioBERT, FinBERT, LegalBERT)
- Multilingual models (XLM-RoBERTa)

Note: This adds significant dependencies and model size (~500MB per model).
Use only when spaCy models are insufficient.
"""

from .engine import TransformerNEREngine, DomainTransformerNEREngine
from .models import TRANSFORMER_MODELS, get_model_for_domain

__all__ = [
    "TransformerNEREngine",
    "DomainTransformerNEREngine",
    "TRANSFORMER_MODELS",
    "get_model_for_domain",
]
