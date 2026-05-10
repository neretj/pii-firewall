"""Catalog of recommended transformer models for different domains and languages.

This provides a curated list of high-quality transformer models for NER,
organized by domain and language.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TransformerModelConfig:
    """Configuration for a transformer NER model."""
    
    model_id: str  # HuggingFace model identifier
    domain: str  # "general", "medical", "financial", "legal"
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
    entity_types=("DISEASE", "DRUG", "CHEMICAL", "GENE", "PROTEIN"),
    description="Biomedical NER - trained on BC5CDR, JNLPBA, NCBI-disease",
    size_mb=440,
)

MEDICAL_EN_CLINICAL = TransformerModelConfig(
    model_id="emilyalsentzer/Bio_ClinicalBERT",
    domain="medical",
    language="en",
    entity_types=("DISEASE", "SYMPTOM", "DRUG", "PROCEDURE"),
    description="Clinical NER - pre-trained on MIMIC-III clinical notes",
    size_mb=440,
)

MEDICAL_ES = TransformerModelConfig(
    model_id="PlanTL-GOB-ES/bsc-bio-ehr-es",
    domain="medical",
    language="es",
    entity_types=("DISEASE", "DRUG", "PROCEDURE", "SYMPTOM"),
    description="Spanish biomedical NER - trained on clinical texts",
    size_mb=420,
)


# =============================================================================
# FINANCIAL NER MODELS
# =============================================================================

FINANCIAL_EN = TransformerModelConfig(
    model_id="ProsusAI/finbert",
    domain="financial",
    language="en",
    entity_types=("ORGANIZATION", "PERSON", "MONEY", "PERCENT", "DATE"),
    description="Financial NER - pre-trained on financial news and reports",
    size_mb=440,
)


# =============================================================================
# LEGAL NER MODELS
# =============================================================================

LEGAL_EN = TransformerModelConfig(
    model_id="nlpaueb/legal-bert-base-uncased",
    domain="legal",
    language="en",
    entity_types=("COURT", "JUDGE", "LAWYER", "CASE", "STATUTE"),
    description="Legal NER - pre-trained on legal documents",
    size_mb=440,
)


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
    
    # Medical
    ("medical", "en"): MEDICAL_EN,
    ("medical", "es"): MEDICAL_ES,
    
    # Financial
    ("financial", "en"): FINANCIAL_EN,
    
    # Legal
    ("legal", "en"): LEGAL_EN,
}


def get_model_for_domain(domain: str, language: str) -> TransformerModelConfig:
    """Get recommended transformer model for domain and language.
    
    Args:
        domain: "general", "medical", "financial", "legal"
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
        print(f"⚠ No {language} model for {domain}. Using multilingual model.")
        return TRANSFORMER_MODELS[multilingual_key]
    
    # Fallback to English if available
    english_key = (domain, "en")
    if english_key in TRANSFORMER_MODELS:
        print(f"⚠ No {language} model for {domain}. Using English model (may have lower accuracy).")
        return TRANSFORMER_MODELS[english_key]
    
    # No model available
    raise ValueError(
        f"No transformer model available for domain '{domain}' and language '{language}'. "
        f"Available: {list(TRANSFORMER_MODELS.keys())}"
    )


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
# ENTITY TYPE → MODEL DOMAIN VOCABULARY
#
# Maps each canonical entity type to the model domain whose NER vocabulary
# can detect it. Used to compute which models a profile actually needs.
#
# Rules:
#   "general"   — detected by standard CoNLL/OntoNotes NER (Presidio/spaCy
#                 already covers these, so the transformer adds little here;
#                 included for completeness in fully-offline mode)
#   "medical"   — requires a biomedical NER model (BioBERT, BC5CDR, etc.)
#   "financial" — requires a financial NER model (FinBERT, etc.)
#   "legal"     — requires a legal NER model (legal-BERT, etc.)
# =============================================================================

ENTITY_TYPE_TO_MODEL_DOMAIN: dict[str, str] = {
    # General / universal — spaCy/Presidio handles these; "general" transformer
    # adds value only for offline/hybrid stacks without Presidio
    "PERSON":            "general",
    "LOCATION":          "general",
    "ADDRESS":           "general",
    "COMPANY_NAME":      "general",
    "DATE":              "general",
    "DATE_TIME":         "general",
    "EMAIL":             "general",
    "PHONE_NUMBER":      "general",
    "SSN":               "general",
    "NATIONAL_ID":       "general",
    "PASSPORT":          "general",
    "DRIVERS_LICENSE":   "general",
    "POSTAL_CODE":       "general",
    "IP_ADDRESS":        "general",
    "URL":               "general",
    "SECRET":            "general",
    "AGE":               "general",

    # Medical — requires biomedical NER (BioBERT, BC5CDR, etc.)
    "DIAGNOSIS":         "medical",
    "DRUG":              "medical",
    "PROCEDURE":         "medical",
    "SYMPTOM":           "medical",
    "LAB_VALUE":         "medical",
    "VITAL_SIGN":        "medical",
    "ANATOMICAL_SITE":   "medical",
    "MEDICAL_RECORD":    "medical",

    # Financial — requires financial NER (FinBERT, etc.)
    "TRANSACTION_AMOUNT": "financial",
    "CURRENCY":           "financial",
    "TRANSACTION_TYPE":   "financial",
    "PERCENTAGE":         "financial",
    "IBAN":               "financial",
    "CREDIT_CARD":        "financial",
    "ACCOUNT_NUMBER":     "financial",
    "ROUTING_NUMBER":     "financial",
    "TAX_ID":             "financial",

    # Legal — requires legal NER (legal-BERT, etc.)
    "CASE_NUMBER":    "legal",
    "STATUTE":        "legal",
    "LEGAL_CITATION": "legal",
    "LEGAL_ENTITY":   "legal",
}


def get_required_model_domains(profile) -> set[str]:
    """Compute the set of model domains needed to fully serve a profile.

    A domain is "needed" if:
      - The profile has a REDACT/PSEUDONYMIZE/MASK/GENERALIZE disposition for
        any entity type in that domain's vocabulary (detection required to act)
      - OR the profile has a KEEP disposition for a medical entity type
        (detection required for disambiguation — prevents spaCy from
        misclassifying e.g. "Parkinson's disease" as a PERSON name)

    The "general" domain is always included as the baseline.

    Args:
        profile: A DomainProfile instance.

    Returns:
        Set of domain strings to load, e.g. {"general", "medical"}.
    """
    from ..profiles.profiles import DispositionAction

    domains: set[str] = {"general"}

    for entity_type, disposition in profile.dispositions.items():
        model_domain = ENTITY_TYPE_TO_MODEL_DOMAIN.get(entity_type)
        if model_domain is None or model_domain == "general":
            continue

        action = disposition.action
        if action != DispositionAction.KEEP:
            # Any active anonymization action → must detect this entity type to act on it.
            domains.add(model_domain)
        else:
            # KEEP on a non-general entity → still load the domain model for two reasons:
            #   1. Disambiguation: prevents the general NER from misclassifying domain
            #      terms as PERSON (e.g. "Parkinson's disease", "Turner syndrome" for
            #      medical; statute/case references for legal).
            #   2. Pass-through correctness: the entity must be detected first so the
            #      anonymization engine can confirm it is in-scope and leave it untouched
            #      rather than silently ignoring it.
            domains.add(model_domain)

    return domains
