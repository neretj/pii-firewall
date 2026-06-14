"""Catalog of recommended transformer models for different domains and languages.

This provides a curated list of high-quality transformer models for NER,
organized by domain and language.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass


@dataclass(frozen=True)
class TransformerModelConfig:
    """Configuration for a transformer NER model."""
    
    model_id: str  # HuggingFace model identifier
    domain: str  # "general" | "medical"
    language: str  # ISO 639-1 code or "multilingual"
    entity_types: tuple[str, ...]  # Entities this model can detect
    description: str
    size_mb: int  # Approximate model size
    
    
# =============================================================================
# GENERAL NER MODELS
# =============================================================================

GENERAL_EN = TransformerModelConfig(
    model_id="dslim/bert-base-NER",
    domain="general",
    language="en",
    entity_types=("PERSON", "ORGANIZATION", "LOCATION", "MISC"),
    description="English NER - fine-tuned on CoNLL-2003",
    size_mb=420,
)

GENERAL_MULTILINGUAL = TransformerModelConfig(
    model_id="Davlan/xlm-roberta-base-ner-hrl",
    domain="general",
    language="multilingual",
    entity_types=("PERSON", "ORGANIZATION", "LOCATION"),
    description="Multilingual NER - 10 languages including ES, EN, FR, DE",
    size_mb=1100,
)

GENERAL_ES = TransformerModelConfig(
    model_id="Davlan/xlm-roberta-base-ner-hrl",
    domain="general",
    language="es",
    entity_types=("PERSON", "ORGANIZATION", "LOCATION", "MISC"),
    description="Spanish NER via multilingual XLM-RoBERTa",
    size_mb=1100,
)

GENERAL_FR = TransformerModelConfig(
    model_id="Jean-Baptiste/camembert-ner",
    domain="general",
    language="fr",
    entity_types=("PERSON", "ORGANIZATION", "LOCATION"),
    description="French NER - CamemBERT fine-tuned on FTB",
    size_mb=440,
)

GENERAL_DE = TransformerModelConfig(
    model_id="dslim/bert-base-NER-uncased",
    domain="general",
    language="de",
    entity_types=("PERSON", "ORGANIZATION", "LOCATION", "MISC"),
    description="German NER - BERT fine-tuned on CoNLL-2003",
    size_mb=420,
)


# =============================================================================
# MEDICAL NER MODELS
# =============================================================================

MEDICAL_EN = TransformerModelConfig(
    model_id="d4data/biomedical-ner-all",
    domain="medical",
    language="en",
    # Actual aggregated labels emitted by this model (B-/I- prefix stripped):
    # Disease_disorder, Sign_symptom, Medication, Diagnostic_procedure,
    # Therapeutic_procedure, Lab_value, Biological_structure, Clinical_event,
    # Family_history, Dosage, History, Outcome, Severity, Activity, ...
    entity_types=(
        "Disease_disorder", "Sign_symptom", "Medication",
        "Diagnostic_procedure", "Therapeutic_procedure", "Lab_value",
        "Biological_structure", "Clinical_event",
    ),
    description=(
        "Biomedical NER (DistilBert) - DistilBERT fine-tuned on MACCROBAT2018; "
        "43-class schema covering diseases, symptoms, medications, procedures, "
        "lab values, anatomical structures and more."
    ),
    size_mb=265,
)

# NOTE: PlanTL-GOB-ES/bsc-bio-ehr-es was removed — it is a masked-language-model
# base checkpoint without a token-classification head (classifier.weight MISSING
# at load time → produces no predictions). For Spanish biomedical NER the code
# falls back to d4data/biomedical-ner-all via the English fallback in
# get_model_for_domain(), which handles cross-language medical terminology well
# (disease/drug names are largely Latin-based and model-agnostic).


# Financial and legal domain NER models are intentionally NOT included.
#
# Transaction amounts, percentages, legal statutes, case citations, and company
# names are not regulated PII — they are public or contextual data that this
# anonymizer must not redact. Loading a 900MB specialised model to detect
# "Article 6 GDPR" or "50,000 euros" (which we then KEEP unchanged) would
# waste memory and add latency with zero privacy benefit.
#
# Structured financial identifiers (IBAN, credit card, account numbers, tax IDs)
# are handled accurately by regex patterns — no NER model needed.
# Company names and organisations are detected by the general CoNLL NER model.


# =============================================================================
# MODEL CATALOG
# =============================================================================

TRANSFORMER_MODELS: dict[tuple[str, str], TransformerModelConfig] = {
    # General
    ("general", "en"): GENERAL_EN,
    ("general", "es"): GENERAL_ES,
    ("general", "fr"): GENERAL_FR,
    ("general", "de"): GENERAL_DE,
    ("general", "multilingual"): GENERAL_MULTILINGUAL,
    
    # Medical — only English model available; Spanish falls back to English
    # via get_model_for_domain() since medical terminology is cross-linguistic.
    ("medical", "en"): MEDICAL_EN,
}


def get_model_for_domain(domain: str, language: str) -> TransformerModelConfig:
    """Get recommended transformer model for domain and language.
    
    Args:
        domain: "general" | "medical"
        language: ISO 639-1 code (or "multilingual")
    
    Returns:
        TransformerModelConfig
    
    Raises:
        ValueError: If no model available for domain/language
    """
    key = (domain, language)
    
    if key in TRANSFORMER_MODELS:
        return TRANSFORMER_MODELS[key]
    
    # Fallback to multilingual if language-specific not available
    multilingual_key = (domain, "multilingual")
    if multilingual_key in TRANSFORMER_MODELS:
        warnings.warn(
            f"No {language} model for domain '{domain}'. Using multilingual model.",
            stacklevel=2,
        )
        return TRANSFORMER_MODELS[multilingual_key]

    # Fallback to English if available
    english_key = (domain, "en")
    if english_key in TRANSFORMER_MODELS:
        warnings.warn(
            f"No {language} model for domain '{domain}'. "
            "Using English model (accuracy may be lower for non-English text).",
            stacklevel=2,
        )
        return TRANSFORMER_MODELS[english_key]
    
    # No model available
    raise ValueError(
        f"No transformer model available for domain '{domain}' and language '{language}'. "
        f"Available: {list(TRANSFORMER_MODELS.keys())}"
    )


def get_domain_for_model_id(model_id: str) -> str:
    """Return the catalog domain for a known model ID, or 'general' for unknown models."""
    for cfg in TRANSFORMER_MODELS.values():
        if cfg.model_id == model_id:
            return cfg.domain
    return "general"


def list_available_models(domain: str | None = None, language: str | None = None) -> list[TransformerModelConfig]:
    """List available transformer models, optionally filtered.
    
    Args:
        domain: Filter by domain (or None for all)
        language: Filter by language (or None for all)
    
    Returns:
        List of matching TransformerModelConfig
    """
    models = []
    
    for (model_domain, model_lang), config in TRANSFORMER_MODELS.items():
        if domain is not None and model_domain != domain:
            continue
        if language is not None and model_lang != language:
            continue
        models.append(config)
    
    return models


# =============================================================================
# ENTITY TYPE → SPECIALIZED MODEL DOMAIN
#
# Maps entity types to the NER model domain required to detect them.
# Only entity types that satisfy ALL of the following criteria appear here:
#   1. Cannot be reliably detected by regex patterns or the general CoNLL NER
#   2. Constitute regulated PII or GDPR Article 9 special-category data
#   3. Require anonymization in at least one domain profile
#
# Entity types absent from this dict are covered by one of:
#   - Regex patterns: PERSON (name patterns), EMAIL, PHONE_NUMBER, SSN, IBAN,
#     CREDIT_CARD, ACCOUNT_NUMBER, NATIONAL_ID, PASSPORT, POSTAL_CODE,
#     IP_ADDRESS, URL, SECRET, TAX_ID
#   - General CoNLL NER (dslim/bert-base-NER): PERSON, COMPANY_NAME (ORG),
#     LOCATION (LOC/GPE)
#   - Not regulated PII: TRANSACTION_AMOUNT, CURRENCY, PERCENTAGE,
#     STATUTE, LEGAL_CITATION, CASE_NUMBER, LEGAL_ENTITY — these are
#     public or contextual data and must NOT be anonymized.
# =============================================================================

ENTITY_TYPE_TO_MODEL_DOMAIN: dict[str, str] = {
    # Medical — GDPR Article 9 special-category data; invisible to general NER
    "DIAGNOSIS":       "medical",
    "DRUG":            "medical",
    "PROCEDURE":       "medical",
    "SYMPTOM":         "medical",
    "LAB_VALUE":       "medical",
    "VITAL_SIGN":      "medical",
    "ANATOMICAL_SITE": "medical",
    "MEDICAL_RECORD":  "medical",
}


def get_required_model_domains(dispositions: dict) -> set[str]:
    """Return the set of specialized NER model domains needed for these dispositions.

    A domain is needed whenever any entity type in the profile's dispositions
    maps to it in ENTITY_TYPE_TO_MODEL_DOMAIN — regardless of action. This
    covers two cases:
      - REDACT/PSEUDONYMIZE/etc.: must detect to act on it.
      - KEEP: must still detect for disambiguation (prevents the general spaCy
        model from misclassifying domain terms as PERSON — e.g. "Parkinson's
        disease", "Turner syndrome", "Article 29 GDPR").

    The caller is responsible for deciding whether to also load the "general"
    baseline transformer (only needed when Presidio/spaCy is NOT running).

    Args:
        dispositions: Mapping of entity_type → EntityDisposition (profile.dispositions).

    Returns:
        Set of specialized domain strings, e.g. {"medical"}.
    """
    domains: set[str] = set()
    for entity_type in dispositions:
        model_domain = ENTITY_TYPE_TO_MODEL_DOMAIN.get(entity_type)
        if model_domain:
            domains.add(model_domain)
    return domains
