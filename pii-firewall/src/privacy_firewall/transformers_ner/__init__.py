"""Transformer-based NER backend (HuggingFace).

Provides two engines:

- :class:`TransformerNEREngine` — wraps any HuggingFace token-classification
  pipeline and maps its labels to canonical entity type constants.
- :class:`DomainTransformerNEREngine` — subclass that applies domain-aware
  label normalisation (currently ``"medical"``).

Active model stack:
- ``dslim/bert-base-NER`` (420 MB) — general CoNLL-2003 NER (PERSON/ORG/LOC).
- ``d4data/biomedical-ner-all`` (265 MB) — 43-class biomedical NER.
- ``Davlan/xlm-roberta-base-ner-hrl`` — multilingual fallback.
- Language-specific models for FR, DE, ES (see ``models.py``).
"""

from .engine import RemoteTransformerNEREngine, TransformerNEREngine, DomainTransformerNEREngine
from .models import TRANSFORMER_MODELS, get_model_for_domain

__all__ = [
    "TransformerNEREngine",
    "DomainTransformerNEREngine",
    "RemoteTransformerNEREngine",
    "TRANSFORMER_MODELS",
    "get_model_for_domain",
]
