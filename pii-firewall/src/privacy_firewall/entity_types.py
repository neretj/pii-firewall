"""Canonical entity type registry.

This is the single source of truth for all entity type string constants used
across the entire system:
  - Pattern engine (locales.py)
  - Backend label mappers (unified_detector.py)
  - Transformer normalizers (transformers_ner/engine.py)
  - Profile dispositions (profiles/presets.py)

Rules:
1. Every entity type string that appears anywhere in the codebase MUST be
   defined here as a constant.
2. All backend label mappers MUST normalize their raw labels to one of these
   constants before emitting an Entity.
3. Profile dispositions MUST reference these constants (or their string values).
4. If a backend emits a label not in this registry, it is unknown and dropped.

Adding a new entity type:
  1. Add a constant here with a clear docstring.
  2. Add it to ALL_ENTITY_TYPES set.
  3. Add disposition entries to any profiles that should handle it.
  4. If needed, add a pattern rule in locales.py or a label mapping in
     unified_detector.py for the relevant backends.
"""

from __future__ import annotations

# =============================================================================
# PERSON / IDENTITY
# =============================================================================

PERSON = "PERSON"
"""Full or partial person name (natural person)."""

# =============================================================================
# CONTACT
# =============================================================================

EMAIL = "EMAIL"
"""Email addresses (any format, any domain)."""

PHONE_NUMBER = "PHONE_NUMBER"
"""Phone numbers — any format, any locale (national, international, mobile, landline).

Canonical name used across all backends. The legacy alias 'PHONE' does NOT exist
as a separate type; all patterns and mappers emit PHONE_NUMBER.
"""

URL = "URL"
"""Web URLs and links."""

# =============================================================================
# NATIONAL IDENTIFIERS
# =============================================================================

NATIONAL_ID = "NATIONAL_ID"
"""Government-issued national identifier: Spanish DNI/NIE, French INSEE,
Italian Codice Fiscale, US driver's license, etc.

Locale-specific subtypes (e.g., 'ES DNI', 'FR INSEE') are NOT separate entity
types — they are all NATIONAL_ID. The locale context is preserved by the pattern
locale tag on the originating EntityPattern.
"""

SSN = "SSN"
"""US Social Security Number (and equivalents used as SSN in other systems)."""

PASSPORT = "PASSPORT"
"""Passport number."""

DRIVERS_LICENSE = "DRIVERS_LICENSE"
"""Driver's license number (any country)."""

# =============================================================================
# FINANCIAL
# =============================================================================

IBAN = "IBAN"
"""International Bank Account Number (ISO 13616)."""

CREDIT_CARD = "CREDIT_CARD"
"""Credit and debit card numbers (PAN)."""

ACCOUNT_NUMBER = "ACCOUNT_NUMBER"
"""Generic bank account or routing number not in IBAN format."""

TAX_ID = "TAX_ID"
"""Tax identification number: US EIN, German Steuernummer, Portuguese NIF, etc."""

TRANSACTION_AMOUNT = "TRANSACTION_AMOUNT"
"""Monetary amounts in a financial transaction context."""

CURRENCY = "CURRENCY"
"""ISO currency codes or currency names (USD, EUR, GBP, etc.)."""

TRANSACTION_TYPE = "TRANSACTION_TYPE"
"""Transaction category: transfer, payment, withdrawal, etc."""

COMPANY_NAME = "COMPANY_NAME"
"""Legal entity / company name (non-natural person)."""

PERCENTAGE = "PERCENTAGE"
"""Percentage figures (interest rates, margins, etc.)."""

# =============================================================================
# TEMPORAL
# =============================================================================

DATE_TIME = "DATE_TIME"
"""Full date-time expressions (includes date-only, time-only, and combined)."""

DATE = "DATE"
"""Date references that are clearly date-only (no time component)."""

AGE = "AGE"
"""Age in years as stated in text ('43 años', '55 years old')."""

# =============================================================================
# LOCATION
# =============================================================================

LOCATION = "LOCATION"
"""Geographic location: city, region, country, landmark."""

ADDRESS = "ADDRESS"
"""Full or partial street address."""

POSTAL_CODE = "POSTAL_CODE"
"""Postal or ZIP code."""

# =============================================================================
# DIGITAL / TECHNICAL
# =============================================================================

IP_ADDRESS = "IP_ADDRESS"
"""IPv4 or IPv6 address."""

MAC_ADDRESS = "MAC_ADDRESS"
"""Network hardware MAC address (48-bit, any separator format)."""

ROUTING_NUMBER = "ROUTING_NUMBER"
"""Bank routing number (ABA/ACH, SWIFT/BIC)."""

SECRET = "SECRET"
"""Secrets, passwords, API keys, tokens, PINs, CVVs."""

LICENSE_PLATE = "LICENSE_PLATE"
"""Vehicle registration / license plate number."""

# =============================================================================
# MEDICAL
# =============================================================================

MEDICAL_RECORD = "MEDICAL_RECORD"
"""Medical record number (MRN, NHC)."""

DIAGNOSIS = "DIAGNOSIS"
"""Medical diagnosis, condition, or ICD code."""

DRUG = "DRUG"
"""Medication name or drug substance."""

PROCEDURE = "PROCEDURE"
"""Medical procedure or surgical intervention."""

LAB_VALUE = "LAB_VALUE"
"""Laboratory test result (e.g., glucose 120 mg/dL)."""

VITAL_SIGN = "VITAL_SIGN"
"""Vital sign measurement (blood pressure, heart rate, temperature)."""

SYMPTOM = "SYMPTOM"
"""Patient-reported symptom or clinical observation."""

ANATOMICAL_SITE = "ANATOMICAL_SITE"
"""Body part or anatomical location."""

# =============================================================================
# LEGAL
# =============================================================================

CASE_NUMBER = "CASE_NUMBER"
"""Court case identifier or docket number."""

STATUTE = "STATUTE"
"""Legal statute, regulation, or code reference."""

LEGAL_CITATION = "LEGAL_CITATION"
"""Case law citation."""

LEGAL_ENTITY = "LEGAL_ENTITY"
"""Court, tribunal, or legal institution."""

# =============================================================================
# MASTER SET (all valid entity type strings)
# =============================================================================

ALL_ENTITY_TYPES: frozenset[str] = frozenset({
    # Person / Identity
    PERSON,
    # Contact
    EMAIL, PHONE_NUMBER, URL,
    # National IDs
    NATIONAL_ID, SSN, PASSPORT, DRIVERS_LICENSE,
    # Financial
    IBAN, CREDIT_CARD, ACCOUNT_NUMBER, TAX_ID,
    TRANSACTION_AMOUNT, CURRENCY, TRANSACTION_TYPE, COMPANY_NAME, PERCENTAGE,
    # Temporal
    DATE_TIME, DATE, AGE,
    # Location
    LOCATION, ADDRESS, POSTAL_CODE,
    # Digital
    IP_ADDRESS, MAC_ADDRESS, ROUTING_NUMBER, SECRET, LICENSE_PLATE,
    # Medical
    MEDICAL_RECORD, DIAGNOSIS, DRUG, PROCEDURE, LAB_VALUE,
    VITAL_SIGN, SYMPTOM, ANATOMICAL_SITE,
    # Legal
    CASE_NUMBER, STATUTE, LEGAL_CITATION, LEGAL_ENTITY,
})


def is_known(entity_type: str) -> bool:
    """Return True if entity_type is in the canonical registry."""
    return entity_type in ALL_ENTITY_TYPES


def validate(entity_type: str) -> str:
    """Return entity_type if known, raise ValueError otherwise."""
    if entity_type not in ALL_ENTITY_TYPES:
        raise ValueError(
            f"Unknown entity type '{entity_type}'. "
            f"Add it to privacy_firewall/entity_types.py first."
        )
    return entity_type
