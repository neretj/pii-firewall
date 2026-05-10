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
    model_id="PlanTL-GOB-ES/roberta-base-bne-finetuned-conll2002-es",
    domain="general",
    language="es",
    entity_types=("PERSON", "ORGANIZATION", "LOCATION", "MISC"),
    description="Spanish NER - fine-tuned on CoNLL-2002",
    size_mb=470,
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
