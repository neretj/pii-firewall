"""Preset domain profiles for common use cases."""

from __future__ import annotations

from .profiles import DomainProfile, EntityDisposition, DispositionAction


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
        # Keep domain-relevant clinical entities
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
        
        # Pseudonymize patient/provider identifiers (reversible for continuity)
        "PERSON": EntityDisposition(
            entity_type="PERSON",
            action=DispositionAction.PSEUDONYMIZE,
            confidence_threshold=0.80,
            description="Patient and provider names",
        ),
        "MEDICAL_RECORD": EntityDisposition(
            entity_type="MEDICAL_RECORD",
            action=DispositionAction.PSEUDONYMIZE,
            description="Medical record numbers (MRN, NHC)",
        ),
        
        # Generalize quasi-identifiers
        "AGE": EntityDisposition(
            entity_type="AGE",
            action=DispositionAction.GENERALIZE,
            parameters={"bucket_size": 10},
            description="Age in years (bucketed by decade)",
        ),
        "DATE": EntityDisposition(
            entity_type="DATE",
            action=DispositionAction.GENERALIZE,
            parameters={"granularity": "year"},
            description="Dates (reduced to year only)",
        ),
        
        # Redact out-of-domain or high-risk identifiers
        "EMAIL": EntityDisposition(
            entity_type="EMAIL",
            action=DispositionAction.REDACT,
            description="Email addresses",
        ),
        "PHONE": EntityDisposition(
            entity_type="PHONE",
            action=DispositionAction.REDACT,
            confidence_threshold=0.35,  # Lower threshold for Presidio phone detection (~0.40)
            description="Phone numbers",
        ),        
        "PHONE_NUMBER": EntityDisposition(
            entity_type="PHONE_NUMBER",
            action=DispositionAction.REDACT,
            confidence_threshold=0.35,  # Lower threshold for Presidio phone detection (~0.40)
            description="Phone numbers (alternative entity type)",
        ),        
        "NATIONAL_ID": EntityDisposition(
            entity_type="NATIONAL_ID",
            action=DispositionAction.REDACT,
            description="National ID numbers (SSN, DNI, etc.)",
        ),
        "SSN": EntityDisposition(
            entity_type="SSN",
            action=DispositionAction.REDACT,
            description="Social Security Numbers",
        ),
        "ES_DNI": EntityDisposition(
            entity_type="ES_DNI",
            action=DispositionAction.PSEUDONYMIZE,
            parameters={},
            description="Spanish DNI/NIF identification numbers",
        ),
        "LOCATION": EntityDisposition(
            entity_type="LOCATION",
            action=DispositionAction.GENERALIZE,
            parameters={"level": "city"},
            description="Geographic locations (cities, regions)",
        ),
        "ADDRESS": EntityDisposition(
            entity_type="ADDRESS",
            action=DispositionAction.REDACT,
            description="Street addresses",
        ),
        "POSTAL_CODE": EntityDisposition(
            entity_type="POSTAL_CODE",
            action=DispositionAction.REDACT,
            description="Postal/ZIP codes",
        ),
        "IP_ADDRESS": EntityDisposition(
            entity_type="IP_ADDRESS",
            action=DispositionAction.REDACT,
            description="IP addresses",
        ),
        "URL": EntityDisposition(
            entity_type="URL",
            action=DispositionAction.REDACT,
            description="Web links and URLs",
        ),
        "SECRET": EntityDisposition(
            entity_type="SECRET",
            action=DispositionAction.REDACT,
            description="Secrets, API keys, and tokens",
        ),
        "DATE_TIME": EntityDisposition(
            entity_type="DATE_TIME",
            action=DispositionAction.GENERALIZE,
            confidence_threshold=0.55,  # Lower threshold for date formats (Presidio scores dd/mm/yyyy at ~0.60)
            parameters={"level": "year"},
            description="Dates and timestamps (birth dates, appointments, etc.)",
        ),
        
        # Redact financial data (out of domain)
        "CREDIT_CARD": EntityDisposition(
            entity_type="CREDIT_CARD",
            action=DispositionAction.REDACT,
            description="Credit card numbers",
        ),
        "IBAN": EntityDisposition(
            entity_type="IBAN",
            action=DispositionAction.REDACT,
            description="Bank account numbers",
        ),
        "TAX_ID": EntityDisposition(
            entity_type="TAX_ID",
            action=DispositionAction.REDACT,
            description="Tax identification numbers",
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
        # Keep domain-relevant financial entities
        "TRANSACTION_AMOUNT": EntityDisposition(
            entity_type="TRANSACTION_AMOUNT",
            action=DispositionAction.KEEP,
            description="Transaction amounts and currencies",
        ),
        "COMPANY_NAME": EntityDisposition(
            entity_type="COMPANY_NAME",
            action=DispositionAction.KEEP,
            description="Company and organization names",
        ),
        "TRANSACTION_TYPE": EntityDisposition(
            entity_type="TRANSACTION_TYPE",
            action=DispositionAction.KEEP,
            description="Transaction categories (transfer, payment, etc.)",
        ),
        "CURRENCY": EntityDisposition(
            entity_type="CURRENCY",
            action=DispositionAction.KEEP,
            description="Currency codes",
        ),
        "DATE": EntityDisposition(
            entity_type="DATE",
            action=DispositionAction.KEEP,
            description="Transaction dates (keep full precision for analysis)",
        ),
        
        # Pseudonymize client identifiers (reversible for audit)
        "PERSON": EntityDisposition(
            entity_type="PERSON",
            action=DispositionAction.PSEUDONYMIZE,
            confidence_threshold=0.75,
            description="Client and employee names",
        ),
        "IBAN": EntityDisposition(
            entity_type="IBAN",
            action=DispositionAction.PSEUDONYMIZE,
            description="Bank account numbers (reversible for audit)",
        ),
        "ACCOUNT_NUMBER": EntityDisposition(
            entity_type="ACCOUNT_NUMBER",
            action=DispositionAction.PSEUDONYMIZE,
            description="Account numbers",
        ),
        "TAX_ID": EntityDisposition(
            entity_type="TAX_ID",
            action=DispositionAction.PSEUDONYMIZE,
            description="Tax IDs (reversible for compliance)",
        ),
        
        # Mask partial visibility for UX
        "CREDIT_CARD": EntityDisposition(
            entity_type="CREDIT_CARD",
            action=DispositionAction.MASK,
            parameters={"visible_digits": 4},
            description="Credit card numbers (show last 4 digits)",
        ),
        
        # Redact out-of-domain data
        "EMAIL": EntityDisposition(
            entity_type="EMAIL",
            action=DispositionAction.REDACT,
            description="Email addresses",
        ),
        "PHONE": EntityDisposition(
            entity_type="PHONE",
            action=DispositionAction.REDACT,
            description="Phone numbers",
        ),
        "ADDRESS": EntityDisposition(
            entity_type="ADDRESS",
            action=DispositionAction.REDACT,
            description="Street addresses",
        ),
        "POSTAL_CODE": EntityDisposition(
            entity_type="POSTAL_CODE",
            action=DispositionAction.REDACT,
            description="Postal codes",
        ),
        "IP_ADDRESS": EntityDisposition(
            entity_type="IP_ADDRESS",
            action=DispositionAction.REDACT,
            description="IP addresses",
        ),
        "URL": EntityDisposition(
            entity_type="URL",
            action=DispositionAction.REDACT,
            description="Web links and URLs",
        ),
        "SECRET": EntityDisposition(
            entity_type="SECRET",
            action=DispositionAction.REDACT,
            description="Secrets, API keys, and tokens",
        ),
        
        # Redact medical data (out of domain)
        "DIAGNOSIS": EntityDisposition(
            entity_type="DIAGNOSIS",
            action=DispositionAction.REDACT,
            description="Medical diagnoses",
        ),
        "DRUG": EntityDisposition(
            entity_type="DRUG",
            action=DispositionAction.REDACT,
            description="Medication names",
        ),
        "MEDICAL_RECORD": EntityDisposition(
            entity_type="MEDICAL_RECORD",
            action=DispositionAction.REDACT,
            description="Medical record numbers",
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
        # Keep domain-relevant legal entities
        "CASE_NUMBER": EntityDisposition(
            entity_type="CASE_NUMBER",
            action=DispositionAction.KEEP,
            description="Case identifiers and docket numbers",
        ),
        "STATUTE": EntityDisposition(
            entity_type="STATUTE",
            action=DispositionAction.KEEP,
            description="Legal statutes and regulations",
        ),
        "LEGAL_CITATION": EntityDisposition(
            entity_type="LEGAL_CITATION",
            action=DispositionAction.KEEP,
            description="Case law citations",
        ),
        "COMPANY_NAME": EntityDisposition(
            entity_type="COMPANY_NAME",
            action=DispositionAction.KEEP,
            description="Organizations (non-natural persons, public record)",
        ),
        
        # Pseudonymize party identifiers
        "PERSON": EntityDisposition(
            entity_type="PERSON",
            action=DispositionAction.PSEUDONYMIZE,
            confidence_threshold=0.85,
            description="Party names (reversible for authorized access)",
        ),
        
        # Generalize dates for privacy
        "DATE": EntityDisposition(
            entity_type="DATE",
            action=DispositionAction.GENERALIZE,
            parameters={"granularity": "month"},
            description="Dates (reduced to month/year)",
        ),
        
        # Redact all personal identifiers
        "EMAIL": EntityDisposition(
            entity_type="EMAIL",
            action=DispositionAction.REDACT,
            description="Email addresses",
        ),
        "PHONE": EntityDisposition(
            entity_type="PHONE",
            action=DispositionAction.REDACT,
            description="Phone numbers",
        ),
        "NATIONAL_ID": EntityDisposition(
            entity_type="NATIONAL_ID",
            action=DispositionAction.REDACT,
            description="National ID numbers",
        ),
        "SSN": EntityDisposition(
            entity_type="SSN",
            action=DispositionAction.REDACT,
            description="Social Security Numbers",
        ),
        "ADDRESS": EntityDisposition(
            entity_type="ADDRESS",
            action=DispositionAction.REDACT,
            description="Street addresses",
        ),
        "POSTAL_CODE": EntityDisposition(
            entity_type="POSTAL_CODE",
            action=DispositionAction.REDACT,
            description="Postal codes",
        ),
        "CREDIT_CARD": EntityDisposition(
            entity_type="CREDIT_CARD",
            action=DispositionAction.REDACT,
            description="Credit card numbers",
        ),
        "IBAN": EntityDisposition(
            entity_type="IBAN",
            action=DispositionAction.REDACT,
            description="Bank account numbers",
        ),
        "TAX_ID": EntityDisposition(
            entity_type="TAX_ID",
            action=DispositionAction.REDACT,
            description="Tax IDs",
        ),
        "IP_ADDRESS": EntityDisposition(
            entity_type="IP_ADDRESS",
            action=DispositionAction.REDACT,
            description="IP addresses",
        ),
        "URL": EntityDisposition(
            entity_type="URL",
            action=DispositionAction.REDACT,
            description="Web links and URLs",
        ),
        "SECRET": EntityDisposition(
            entity_type="SECRET",
            action=DispositionAction.REDACT,
            description="Secrets, API keys, and tokens",
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
        "PERSON": EntityDisposition(entity_type="PERSON", action=DispositionAction.PSEUDONYMIZE),
        "EMAIL": EntityDisposition(entity_type="EMAIL", action=DispositionAction.REDACT),
        "PHONE": EntityDisposition(entity_type="PHONE", action=DispositionAction.REDACT),
        "PHONE_NUMBER": EntityDisposition(entity_type="PHONE_NUMBER", action=DispositionAction.REDACT),
        "NATIONAL_ID": EntityDisposition(entity_type="NATIONAL_ID", action=DispositionAction.REDACT),
        "SSN": EntityDisposition(entity_type="SSN", action=DispositionAction.REDACT),
        "IBAN": EntityDisposition(entity_type="IBAN", action=DispositionAction.REDACT),
        "TAX_ID": EntityDisposition(entity_type="TAX_ID", action=DispositionAction.REDACT),
        "ACCOUNT_NUMBER": EntityDisposition(entity_type="ACCOUNT_NUMBER", action=DispositionAction.REDACT),
        "CREDIT_CARD": EntityDisposition(entity_type="CREDIT_CARD", action=DispositionAction.MASK),
        "ES_DNI": EntityDisposition(entity_type="ES_DNI", action=DispositionAction.PSEUDONYMIZE),
        "ADDRESS": EntityDisposition(entity_type="ADDRESS", action=DispositionAction.REDACT),
        "POSTAL_CODE": EntityDisposition(entity_type="POSTAL_CODE", action=DispositionAction.REDACT),
        "IP_ADDRESS": EntityDisposition(entity_type="IP_ADDRESS", action=DispositionAction.REDACT),
        "URL": EntityDisposition(entity_type="URL", action=DispositionAction.REDACT),
        "SECRET": EntityDisposition(entity_type="SECRET", action=DispositionAction.REDACT),
        "DATE": EntityDisposition(
            entity_type="DATE",
            action=DispositionAction.GENERALIZE,
            parameters={"granularity": "year"},
        ),
        "DATE_TIME": EntityDisposition(
            entity_type="DATE_TIME",
            action=DispositionAction.GENERALIZE,
            parameters={"level": "year"},
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
                    action=DispositionAction(disp.get("action", "redact")),
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
