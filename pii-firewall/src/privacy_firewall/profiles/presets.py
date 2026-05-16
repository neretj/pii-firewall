"""Preset domain profiles for common use cases."""

from __future__ import annotations

from .profiles import DomainProfile, EntityDisposition, DispositionAction

# Presidio scores phone numbers at ~0.40 — lower the threshold so they are
# processed even when the backend returns a modest confidence value.
_PHONE_THRESHOLD = 0.35

# Presidio scores many date patterns at ~0.60; use a slightly lower gate.
_DATE_THRESHOLD = 0.55


# =============================================================================
# UNIVERSAL BASE DISPOSITIONS
#
# Every profile starts from this baseline. It covers the universal PII types
# that should always be handled — regardless of domain. Domain profiles
# override specific entries and add domain-specific ones on top.
#
# Rationale for each default action:
#   PERSON          → PSEUDONYMIZE  reversible token; needed for cross-turn continuity
#   EMAIL           → PSEUDONYMIZE  reversible token; LLM may need to reference it
#   PHONE_NUMBER    → PSEUDONYMIZE  reversible token
#   NATIONAL_ID     → PSEUDONYMIZE  reversible token; highest risk but still needs rehydration
#   SSN             → PSEUDONYMIZE  reversible token
#   IBAN            → PSEUDONYMIZE  reversible token; domain profiles control scope via token_scope
#   CREDIT_CARD     → MASK          partial visibility sufficient; last 4 digits kept
#   ACCOUNT_NUMBER  → PSEUDONYMIZE  reversible token
#   TAX_ID          → PSEUDONYMIZE  reversible token
#   ADDRESS         → PSEUDONYMIZE  reversible token; precise location, high re-identification risk
#   POSTAL_CODE     → PSEUDONYMIZE  reversible token; quasi-identifier
#   LOCATION        → GENERALIZE    useful at city level, not at street level (one-way)
#   IP_ADDRESS      → PSEUDONYMIZE  reversible token; digital identifier
#   URL             → PSEUDONYMIZE  reversible token; may embed credentials or session data
#   SECRET          → PSEUDONYMIZE  reversible token; passwords/keys need rehydration in context
#   DATE            → GENERALIZE    quasi-identifier; year granularity safe by default (one-way)
#   DATE_TIME       → GENERALIZE    idem — full timestamp is high-risk (one-way)
#
# Token scope (thread / case / tenant) is NOT encoded in the action.
# It is configured at the profile level via DomainProfile.token_scope.
# =============================================================================

_UNIVERSAL_DISPOSITIONS: dict[str, EntityDisposition] = {
    "PERSON": EntityDisposition(
        entity_type="PERSON",
        action=DispositionAction.PSEUDONYMIZE,
        confidence_threshold=0.75,
        description="Person names",
    ),
    "EMAIL": EntityDisposition(
        entity_type="EMAIL",
        action=DispositionAction.PSEUDONYMIZE,
        description="Email addresses",
    ),
    "PHONE_NUMBER": EntityDisposition(
        entity_type="PHONE_NUMBER",
        action=DispositionAction.PSEUDONYMIZE,
        confidence_threshold=_PHONE_THRESHOLD,
        description="Phone numbers",
    ),
    "NATIONAL_ID": EntityDisposition(
        entity_type="NATIONAL_ID",
        action=DispositionAction.PSEUDONYMIZE,
        description="National ID numbers (DNI, INSEE, Codice Fiscale, etc.)",
    ),
    "SSN": EntityDisposition(
        entity_type="SSN",
        action=DispositionAction.PSEUDONYMIZE,
        description="Social Security Numbers",
    ),
    "IBAN": EntityDisposition(
        entity_type="IBAN",
        action=DispositionAction.PSEUDONYMIZE,
        description="Bank account numbers (IBAN)",
    ),
    "CREDIT_CARD": EntityDisposition(
        entity_type="CREDIT_CARD",
        action=DispositionAction.MASK,
        parameters={"visible_end": 4},
        description="Credit/debit card numbers (last 4 digits visible)",
    ),
    "ACCOUNT_NUMBER": EntityDisposition(
        entity_type="ACCOUNT_NUMBER",
        action=DispositionAction.PSEUDONYMIZE,
        description="Bank account numbers and routing identifiers",
    ),
    "TAX_ID": EntityDisposition(
        entity_type="TAX_ID",
        action=DispositionAction.PSEUDONYMIZE,
        description="Tax identification numbers",
    ),
    "ADDRESS": EntityDisposition(
        entity_type="ADDRESS",
        action=DispositionAction.PSEUDONYMIZE,
        description="Street addresses",
    ),
    "POSTAL_CODE": EntityDisposition(
        entity_type="POSTAL_CODE",
        action=DispositionAction.PSEUDONYMIZE,
        description="Postal / ZIP codes",
    ),
    "LOCATION": EntityDisposition(
        entity_type="LOCATION",
        action=DispositionAction.GENERALIZE,
        parameters={"level": "city"},
        description="Geographic locations (generalized to city level)",
    ),
    "IP_ADDRESS": EntityDisposition(
        entity_type="IP_ADDRESS",
        action=DispositionAction.PSEUDONYMIZE,
        description="IP addresses",
    ),
    "URL": EntityDisposition(
        entity_type="URL",
        action=DispositionAction.PSEUDONYMIZE,
        description="Web links and URLs",
    ),
    "SECRET": EntityDisposition(
        entity_type="SECRET",
        action=DispositionAction.PSEUDONYMIZE,
        description="Secrets, API keys, tokens, PINs, CVVs",
    ),
    "DATE": EntityDisposition(
        entity_type="DATE",
        action=DispositionAction.GENERALIZE,
        parameters={"granularity": "year"},
        description="Dates (reduced to year only)",
    ),
    "DATE_TIME": EntityDisposition(
        entity_type="DATE_TIME",
        action=DispositionAction.GENERALIZE,
        confidence_threshold=_DATE_THRESHOLD,
        parameters={"level": "year"},
        description="Date-time expressions (reduced to year)",
    ),
    "PASSPORT": EntityDisposition(
        entity_type="PASSPORT",
        action=DispositionAction.PSEUDONYMIZE,
        description="Passport numbers",
    ),
    "DRIVERS_LICENSE": EntityDisposition(
        entity_type="DRIVERS_LICENSE",
        action=DispositionAction.PSEUDONYMIZE,
        description="Driver's license numbers",
    ),
    "MAC_ADDRESS": EntityDisposition(
        entity_type="MAC_ADDRESS",
        action=DispositionAction.PSEUDONYMIZE,
        description="Network hardware MAC addresses",
    ),
    "ROUTING_NUMBER": EntityDisposition(
        entity_type="ROUTING_NUMBER",
        action=DispositionAction.PSEUDONYMIZE,
        description="Bank routing numbers",
    ),
    "AGE": EntityDisposition(
        entity_type="AGE",
        action=DispositionAction.GENERALIZE,
        parameters={"bucket_size": 10},
        description="Age in years (bucketed by decade)",
    ),
}


# =============================================================================
# HEALTHCARE PROFILE
# =============================================================================

HEALTHCARE_PROFILE = DomainProfile(
    name="healthcare",
    description="Healthcare domain: keep medical data, anonymize patient identifiers",
    defensive_cleanup_enabled=True,
    token_scope="tenant",
    entity_similarity_threshold=0.80,
    linguistic_filter_enabled=True,
    domain_recognizers=["medical_entities", "drug_names", "procedures"],
    dispositions={
        **_UNIVERSAL_DISPOSITIONS,

        # Healthcare overrides — stricter PERSON threshold for clinical context
        "PERSON": EntityDisposition(
            entity_type="PERSON",
            action=DispositionAction.PSEUDONYMIZE,
            confidence_threshold=0.80,
            description="Patient and provider names",
        ),
        # DATE kept at year-level by universal default; only override description
        "DATE": EntityDisposition(
            entity_type="DATE",
            action=DispositionAction.GENERALIZE,
            parameters={"granularity": "year"},
            description="Dates (reduced to year — birth dates, admission dates)",
        ),
        # CREDIT_CARD defaults to MASK in universal; override to PSEUDONYMIZE in
        # healthcare because financial data is fully out of domain here and a
        # masked value (****1111) has no clinical relevance.
        "CREDIT_CARD": EntityDisposition(
            entity_type="CREDIT_CARD",
            action=DispositionAction.PSEUDONYMIZE,
            description="Credit card numbers (out of domain — pseudonymized)",
        ),
        # Domain-specific: keep all clinical entities
        "DIAGNOSIS": EntityDisposition(
            entity_type="DIAGNOSIS",
            action=DispositionAction.KEEP,
            description="Medical diagnoses and conditions (ICD codes, free text)",
        ),
        "DRUG": EntityDisposition(
            entity_type="DRUG",
            action=DispositionAction.KEEP,
            description="Medication names and dosages",
        ),
        "PROCEDURE": EntityDisposition(
            entity_type="PROCEDURE",
            action=DispositionAction.KEEP,
            description="Medical procedures and treatments",
        ),
        "LAB_VALUE": EntityDisposition(
            entity_type="LAB_VALUE",
            action=DispositionAction.KEEP,
            description="Laboratory test results",
        ),
        "VITAL_SIGN": EntityDisposition(
            entity_type="VITAL_SIGN",
            action=DispositionAction.KEEP,
            description="Vital signs (blood pressure, temperature, etc.)",
        ),
        "SYMPTOM": EntityDisposition(
            entity_type="SYMPTOM",
            action=DispositionAction.KEEP,
            description="Patient-reported symptoms",
        ),

        # Pseudonymize medical record numbers for cross-turn continuity
        "MEDICAL_RECORD": EntityDisposition(
            entity_type="MEDICAL_RECORD",
            action=DispositionAction.PSEUDONYMIZE,
            description="Medical record numbers (MRN, NHC)",
        ),

        # Generalize age for re-identification risk
        "AGE": EntityDisposition(
            entity_type="AGE",
            action=DispositionAction.GENERALIZE,
            parameters={"bucket_size": 10},
            description="Age in years (bucketed by decade)",
        ),

        # Bibliographic identifiers — keep untouched; they are NOT patient data
        "DOI": EntityDisposition(
            entity_type="DOI",
            action=DispositionAction.KEEP,
            description="DOI references to academic publications (must not be anonymized)",
        ),
        "PMID": EntityDisposition(
            entity_type="PMID",
            action=DispositionAction.KEEP,
            description="PubMed identifiers for biomedical literature (must not be anonymized)",
        ),
    },
)


# =============================================================================
# FINANCE PROFILE
# =============================================================================

FINANCE_PROFILE = DomainProfile(
    name="finance",
    description="Finance domain: keep transaction data, anonymize client identifiers",
    defensive_cleanup_enabled=True,
    token_scope="tenant",
    entity_similarity_threshold=0.75,
    linguistic_filter_enabled=True,
    domain_recognizers=["financial_entities", "transaction_patterns"],
    dispositions={
        **_UNIVERSAL_DISPOSITIONS,

        # Finance overrides — keep transaction-relevant data, pseudonymize financials
        "DATE": EntityDisposition(
            entity_type="DATE",
            action=DispositionAction.KEEP,
            description="Transaction dates (keep full precision for analysis)",
        ),
        "DATE_TIME": EntityDisposition(
            entity_type="DATE_TIME",
            action=DispositionAction.GENERALIZE,
            parameters={"level": "year"},
            description="Date-time expressions (generalized to year)",
        ),
        "IBAN": EntityDisposition(
            entity_type="IBAN",
            action=DispositionAction.PSEUDONYMIZE,
            description="Bank account numbers (reversible for audit)",
        ),
        "ACCOUNT_NUMBER": EntityDisposition(
            entity_type="ACCOUNT_NUMBER",
            action=DispositionAction.PSEUDONYMIZE,
            description="Account numbers (reversible for audit)",
        ),
        "TAX_ID": EntityDisposition(
            entity_type="TAX_ID",
            action=DispositionAction.PSEUDONYMIZE,
            description="Tax IDs (reversible for compliance)",
        ),

        # Domain-specific: keep company names (detected by general NER as ORG)
        # Structured financial identifiers (IBAN, ACCOUNT_NUMBER, TAX_ID) are
        # handled by the universal dispositions above.
        # Transaction amounts, currencies, and percentages are not regulated PII
        # and are not anonymized.
        "COMPANY_NAME": EntityDisposition(
            entity_type="COMPANY_NAME",
            action=DispositionAction.KEEP,
            description="Company and organization names (public record, not PII)",
        ),

        # Pseudonymize medical data that leaks into finance context.
        # Biomedical NER models score lower than regex, so use threshold 0.45.
        "DIAGNOSIS": EntityDisposition(
            entity_type="DIAGNOSIS",
            action=DispositionAction.PSEUDONYMIZE,
            confidence_threshold=0.45,
            description="Medical diagnoses (out of domain)",
        ),
        "SYMPTOM": EntityDisposition(
            entity_type="SYMPTOM",
            action=DispositionAction.PSEUDONYMIZE,
            confidence_threshold=0.45,
            description="Medical symptoms (cross-domain leakage)",
        ),
        "DRUG": EntityDisposition(
            entity_type="DRUG",
            action=DispositionAction.PSEUDONYMIZE,
            confidence_threshold=0.45,
            description="Medication names (out of domain)",
        ),
        "PROCEDURE": EntityDisposition(
            entity_type="PROCEDURE",
            action=DispositionAction.PSEUDONYMIZE,
            confidence_threshold=0.45,
            description="Medical procedures (out of domain)",
        ),
        "MEDICAL_RECORD": EntityDisposition(
            entity_type="MEDICAL_RECORD",
            action=DispositionAction.PSEUDONYMIZE,
            description="Medical record numbers (out of domain)",
        ),
    },
)


# =============================================================================
# LEGAL PROFILE
# =============================================================================

LEGAL_PROFILE = DomainProfile(
    name="legal",
    description="Legal domain: keep case details, anonymize party identifiers",
    defensive_cleanup_enabled=True,
    token_scope="tenant",
    entity_similarity_threshold=0.85,  # Strict matching
    linguistic_filter_enabled=True,
    domain_recognizers=["legal_entities", "case_citations"],
    dispositions={
        **_UNIVERSAL_DISPOSITIONS,

        # Legal overrides — stricter PERSON threshold, dates at month granularity
        "PERSON": EntityDisposition(
            entity_type="PERSON",
            action=DispositionAction.PSEUDONYMIZE,
            confidence_threshold=0.85,
            description="Party names (reversible for authorized access)",
        ),
        "DATE": EntityDisposition(
            entity_type="DATE",
            action=DispositionAction.GENERALIZE,
            parameters={"granularity": "month"},
            description="Dates (reduced to month/year for legal filings)",
        ),
        # DATE_TIME — NLP backends (Presidio/spaCy) typically label calendar dates
        # as DATE_TIME rather than DATE.  Override universal year-level to month-level
        # so all date-like spans are consistently reduced to month/year in legal docs.
        "DATE_TIME": EntityDisposition(
            entity_type="DATE_TIME",
            action=DispositionAction.GENERALIZE,
            confidence_threshold=_DATE_THRESHOLD,
            parameters={"granularity": "month"},
            description="Date-time expressions (reduced to month/year for legal filings)",
        ),
        # CREDIT_CARD defaults to MASK in universal; override to PSEUDONYMIZE in
        # legal because a masked value has no relevance in legal documents.
        "CREDIT_CARD": EntityDisposition(
            entity_type="CREDIT_CARD",
            action=DispositionAction.PSEUDONYMIZE,
            description="Credit card numbers",
        ),

        # Domain-specific: keep company names (courts, firms) detected by general NER.
        # Legal statutes ("Article 6 GDPR"), case citations ("Smith v. Jones"),
        # and case numbers are public record — not regulated PII, never anonymized.
        "COMPANY_NAME": EntityDisposition(
            entity_type="COMPANY_NAME",
            action=DispositionAction.KEEP,
            description="Organizations — courts, firms, agencies (public record, not PII)",
        ),

        # Cross-domain medical leakage — legal documents routinely contain
        # medical information (injury cases, malpractice, insurance disputes)
        # that must be anonymized to protect parties.
        # Biomedical NER models (d4data) produce lower confidence scores than
        # rule-based detectors, so use a relaxed threshold of 0.45.
        "DIAGNOSIS": EntityDisposition(
            entity_type="DIAGNOSIS",
            action=DispositionAction.PSEUDONYMIZE,
            confidence_threshold=0.45,
            description="Medical diagnoses (injury/malpractice cross-domain leakage)",
        ),
        "SYMPTOM": EntityDisposition(
            entity_type="SYMPTOM",
            action=DispositionAction.PSEUDONYMIZE,
            confidence_threshold=0.45,
            description="Medical symptoms (cross-domain leakage)",
        ),
        "DRUG": EntityDisposition(
            entity_type="DRUG",
            action=DispositionAction.PSEUDONYMIZE,
            confidence_threshold=0.45,
            description="Medication names (cross-domain leakage)",
        ),
        "PROCEDURE": EntityDisposition(
            entity_type="PROCEDURE",
            action=DispositionAction.PSEUDONYMIZE,
            confidence_threshold=0.45,
            description="Medical procedures (cross-domain leakage)",
        ),
        "MEDICAL_RECORD": EntityDisposition(
            entity_type="MEDICAL_RECORD",
            action=DispositionAction.PSEUDONYMIZE,
            description="Medical record numbers (cross-domain leakage)",
        ),
    },
)


# =============================================================================
# GENERIC PROFILE (DEFAULT)
# =============================================================================

GENERIC_PROFILE = DomainProfile(
    name="generic",
    description="General-purpose profile: anonymize common identifiers while keeping content useful.",
    defensive_cleanup_enabled=True,
    token_scope="tenant",
    entity_similarity_threshold=0.75,
    linguistic_filter_enabled=True,
    dispositions={
        **_UNIVERSAL_DISPOSITIONS,

        # Medical entities — redact all; a generic profile makes no assumption
        # about domain context so any medical data is treated as sensitive PII.
        "DIAGNOSIS": EntityDisposition(
            entity_type="DIAGNOSIS",
            action=DispositionAction.PSEUDONYMIZE,
            description="Medical diagnoses and conditions",
        ),
        "DRUG": EntityDisposition(
            entity_type="DRUG",
            action=DispositionAction.PSEUDONYMIZE,
            description="Medication names",
        ),
        "PROCEDURE": EntityDisposition(
            entity_type="PROCEDURE",
            action=DispositionAction.PSEUDONYMIZE,
            description="Medical procedures",
        ),
        "SYMPTOM": EntityDisposition(
            entity_type="SYMPTOM",
            action=DispositionAction.PSEUDONYMIZE,
            description="Patient-reported symptoms",
        ),
        "MEDICAL_RECORD": EntityDisposition(
            entity_type="MEDICAL_RECORD",
            action=DispositionAction.PSEUDONYMIZE,
            description="Medical record numbers",
        ),
    },
)


PRESET_PROFILES: dict[str, DomainProfile] = {
    "generic": GENERIC_PROFILE,
    "healthcare": HEALTHCARE_PROFILE,
    "finance": FINANCE_PROFILE,
    "legal": LEGAL_PROFILE,
}


def list_preset_profiles() -> list[str]:
    """Return all available built-in preset names."""
    return list(PRESET_PROFILES.keys())


def get_preset_profile(name: str) -> DomainProfile:
    """Get a built-in profile by name."""
    profile = PRESET_PROFILES.get(name)
    if profile is None:
        raise ValueError(f"Unknown preset profile: {name}. Choose from {list_preset_profiles()}")
    return profile


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_custom_profile(
    name: str,
    base_profile: DomainProfile | None = None,
    **kwargs,
) -> DomainProfile:
    """Create a custom profile, optionally based on a preset.
    
    Args:
        name: Profile name
        base_profile: Base profile to extend (or None for blank)
        **kwargs: Override profile attributes
    
    Example:
        # Extend healthcare profile with stricter similarity threshold
        custom = create_custom_profile(
            name="healthcare_strict",
            base_profile=HEALTHCARE_PROFILE,
            entity_similarity_threshold=0.9,
        )
    """
    if base_profile is None:
        return DomainProfile(name=name, **kwargs)

    dispositions = dict(base_profile.dispositions)
    custom_dispositions = kwargs.pop("dispositions", None)

    if custom_dispositions:
        for entity_type, disp in custom_dispositions.items():
            if isinstance(disp, EntityDisposition):
                dispositions[entity_type] = disp
            else:
                dispositions[entity_type] = EntityDisposition(
                    entity_type=entity_type,
                    action=DispositionAction(disp.get("action", "pseudonymize")),
                    confidence_threshold=disp.get("confidence_threshold", 0.75),
                    parameters=disp.get("parameters", {}),
                    description=disp.get("description", ""),
                )

    return DomainProfile(
        name=name,
        dispositions=dispositions,
        defensive_cleanup_enabled=kwargs.get("defensive_cleanup_enabled", base_profile.defensive_cleanup_enabled),
        token_scope=kwargs.get("token_scope", base_profile.token_scope),
        entity_similarity_threshold=kwargs.get("entity_similarity_threshold", base_profile.entity_similarity_threshold),
        linguistic_filter_enabled=kwargs.get("linguistic_filter_enabled", base_profile.linguistic_filter_enabled),
        domain_recognizers=kwargs.get("domain_recognizers", list(base_profile.domain_recognizers)),
        description=kwargs.get("description", base_profile.description),
    )
