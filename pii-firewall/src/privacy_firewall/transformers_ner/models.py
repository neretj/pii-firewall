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

MEDICAL_EN_CLINICAL = TransformerModelConfig(
    model_id="samrawal/bert-base-uncased_clinical-ner",
    domain="medical",
    language="en",
    # Labels: problem (→DIAGNOSIS), treatment (→PROCEDURE), test (→LAB_VALUE)
    entity_types=("problem", "treatment", "test"),
    description=(
        "Clinical NER (BERT) - fine-tuned on i2b2/n2c2 clinical notes; "
        "compact 3-class schema (problem/treatment/test) with high precision "
        "on EHR and discharge summary text."
    ),
    size_mb=420,
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

# NOTE: ProsusAI/finbert is a SENTIMENT classifier (positive/negative/neutral),
# NOT a token classifier. It cannot be used for NER.
# tner/roberta-large-ontonotes5 is a RobertaForTokenClassification model trained
# on OntoNotes 5.0, which includes MONEY, PERCENT, ORG, PERSON, DATE and LAW labels
# — the most useful label set for financial and legal document NER.
FINANCIAL_EN = TransformerModelConfig(
    model_id="tner/roberta-large-ontonotes5",
    domain="financial",
    language="en",
    # OntoNotes 5.0 label set (aggregated, after B-/I- strip):
    # PERSON, ORG, MONEY, PERCENT, DATE, TIME, GPE, LOC, FAC, NORP,
    # LAW, CARDINAL, ORDINAL, QUANTITY, PRODUCT, WORK_OF_ART, EVENT, LANGUAGE
    entity_types=("MONEY", "PERCENT", "ORGANIZATION", "PERSON", "DATE", "LAW"),
    description=(
        "Broad-coverage NER (RoBERTa-large) trained on OntoNotes 5.0. "
        "Detects MONEY and PERCENT in prose (\"transferred $50k\", \"15% interest\") "
        "plus ORG, PERSON, DATE, and legal citations (LAW label). "
        "Used for financial and legal domains."
    ),
    size_mb=1400,
)


# =============================================================================
# LEGAL NER MODELS
# =============================================================================

# NOTE: nlpaueb/legal-bert-base-uncased is a masked language model (BertForPreTraining)
# with dummy labels LABEL_0/LABEL_1 — it is NOT fine-tuned for NER.
# We reuse tner/roberta-large-ontonotes5 because OntoNotes includes the LAW label
# which captures statutory references and legal citations in prose.
# The normalizer maps LAW→STATUTE and ORG→LEGAL_ENTITY for this domain.
LEGAL_EN = TransformerModelConfig(
    model_id="tner/roberta-large-ontonotes5",
    domain="legal",
    language="en",
    entity_types=("LAW", "ORGANIZATION", "PERSON", "DATE"),
    description=(
        "Broad-coverage NER (RoBERTa-large) trained on OntoNotes 5.0. "
        "The LAW label detects statutory references (\"42 U.S.C. § 1983\", "
        "\"Article 6 GDPR\"); ORG maps to LEGAL_ENTITY (courts, firms, agencies). "
        "Shared model with financial domain — only loaded once when both are active."
    ),
    size_mb=1400,
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
# Only includes types that CANNOT be reliably detected by the pattern engine
# (regex) or the general-purpose spaCy/Presidio baseline.
#
# Absent from this dict → already covered by patterns or Presidio:
#   PERSON, LOCATION, ADDRESS, DATE, DATE_TIME, EMAIL, PHONE_NUMBER,
#   SSN, IBAN, CREDIT_CARD, ACCOUNT_NUMBER, NATIONAL_ID, PASSPORT,
#   POSTAL_CODE, IP_ADDRESS, URL, SECRET, TAX_ID, COMPANY_NAME, AGE
#   (all regex-detectable or handled by CoNLL/OntoNotes spaCy)
#
# Domains:
#   "medical"   — biomedical NER (BioBERT, BC5CDR, BiomedNER, etc.)
#   "financial" — financial NER for SEMANTIC amounts/types (FinBERT, etc.)
#                 Note: structured financial identifiers (IBAN, card numbers)
#                 are captured by patterns — only unstructured semantic
#                 entities need FinBERT.
#   "legal"     — legal NER (legal-BERT, etc.)
# =============================================================================

ENTITY_TYPE_TO_MODEL_DOMAIN: dict[str, str] = {
    # Medical — biomedical vocabulary invisible to general NER
    "DIAGNOSIS":       "medical",
    "DRUG":            "medical",
    "PROCEDURE":       "medical",
    "SYMPTOM":         "medical",
    "LAB_VALUE":       "medical",
    "VITAL_SIGN":      "medical",
    "ANATOMICAL_SITE": "medical",
    "MEDICAL_RECORD":  "medical",

    # Financial (semantic) — amounts and transaction context that FinBERT
    # recognises in prose ("transferred five hundred euros") where regex fails
    "TRANSACTION_AMOUNT": "financial",
    "CURRENCY":            "financial",
    "TRANSACTION_TYPE":    "financial",
    "PERCENTAGE":          "financial",

    # Legal — case references and statutory citations
    "CASE_NUMBER":    "legal",
    "STATUTE":        "legal",
    "LEGAL_CITATION": "legal",
    "LEGAL_ENTITY":   "legal",
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
        Set of specialized domain strings, e.g. {"medical", "legal"}.
    """
    domains: set[str] = set()
    for entity_type in dispositions:
        model_domain = ENTITY_TYPE_TO_MODEL_DOMAIN.get(entity_type)
        if model_domain:
            domains.add(model_domain)
    return domains
