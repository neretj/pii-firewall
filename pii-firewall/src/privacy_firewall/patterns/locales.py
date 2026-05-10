"""Locale-specific pattern definitions.

This module contains all regex patterns organized by locale.
Each locale file defines patterns for that region's document formats.

Adding new patterns:
1. Add pattern to appropriate locale section below
2. Or create a new locale section
3. Patterns are automatically loaded by PatternCatalog

For company-specific patterns, use PatternCatalog.add_pattern() at runtime.
"""

from __future__ import annotations

import re
from ..patterns.catalog import EntityPattern
from .. import entity_types as ET


# =============================================================================
# GLOBAL PATTERNS (apply to all locales)
# =============================================================================

GLOBAL_EMAIL = EntityPattern(
    entity_type=ET.EMAIL,
    locale="GLOBAL",
    pattern=re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    confidence=1.0,
    description="Email addresses (global)",
)

GLOBAL_IP_V4 = EntityPattern(
    entity_type=ET.IP_ADDRESS,
    locale="GLOBAL",
    pattern=re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    confidence=0.9,
    description="IPv4 addresses",
)

GLOBAL_IP_V6 = EntityPattern(
    entity_type=ET.IP_ADDRESS,
    locale="GLOBAL",
    pattern=re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"),
    confidence=0.95,
    description="IPv6 addresses",
)

GLOBAL_CREDIT_CARD = EntityPattern(
    entity_type=ET.CREDIT_CARD,
    locale="GLOBAL",
    pattern=re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    confidence=0.8,
    context_words=("card", "credit", "visa", "mastercard", "amex"),
    description="Credit card numbers (Luhn validation recommended)",
)


# =============================================================================
# SPANISH PATTERNS (ES)
# =============================================================================

ES_DNI = EntityPattern(
    entity_type=ET.NATIONAL_ID,
    locale="ES",
    pattern=re.compile(r"\b\d{8}[A-Z]\b"),
    confidence=1.0,
    context_words=("dni", "documento", "identidad"),
    description="Spanish DNI (Documento Nacional de Identidad)",
)

ES_NIE = EntityPattern(
    entity_type=ET.NATIONAL_ID,
    locale="ES",
    pattern=re.compile(r"\b[XYZ]\d{7}[A-Z]\b"),
    confidence=1.0,
    context_words=("nie", "extranjero"),
    description="Spanish NIE (Número de Identificación de Extranjero)",
)

ES_PHONE_MOBILE = EntityPattern(
    entity_type=ET.PHONE_NUMBER,
    locale="ES",
    pattern=re.compile(r"\b(?:\+34\s?)?[67]\d{8}\b"),
    confidence=1.0,
    description="Spanish mobile phone numbers",
)

ES_PHONE_LANDLINE = EntityPattern(
    entity_type=ET.PHONE_NUMBER,
    locale="ES",
    pattern=re.compile(r"\b(?:\+34\s?)?[89]\d{8}\b"),
    confidence=1.0,
    description="Spanish landline phone numbers",
)

ES_SOCIAL_SECURITY = EntityPattern(
    entity_type=ET.SSN,
    locale="ES",
    pattern=re.compile(r"\b\d{12}\b"),
    confidence=0.7,
    context_words=("seguridad social", "ss", "nass"),
    description="Spanish Social Security Number",
)

ES_IBAN = EntityPattern(
    entity_type=ET.IBAN,
    locale="ES",
    pattern=re.compile(r"\bES\d{2}\s?\d{4}\s?\d{4}\s?\d{2}\s?\d{10}\b"),
    confidence=0.95,
    context_words=("iban", "cuenta", "bancaria"),
    description="Spanish IBAN",
)

ES_POSTAL_CODE = EntityPattern(
    entity_type=ET.POSTAL_CODE,
    locale="ES",
    pattern=re.compile(r"\b\d{5}\b"),
    confidence=0.6,
    context_words=("cp", "código postal"),
    description="Spanish postal code",
)

ES_LICENSE_PLATE = EntityPattern(
    entity_type=ET.LICENSE_PLATE,
    locale="ES",
    pattern=re.compile(r"\b\d{4}\s?[A-Z]{3}\b"),
    confidence=0.8,
    context_words=("matrícula", "coche", "vehículo"),
    description="Spanish vehicle license plate",
)

ES_AGE = EntityPattern(
    entity_type=ET.AGE,
    locale="ES",
    pattern=re.compile(r"\b(\d{1,3})\s*(?:años?|a\u00f1os?)\b", re.IGNORECASE),
    confidence=0.9,
    description="Age in Spanish (años)",
)

ES_MEDICAL_RECORD = EntityPattern(
    entity_type=ET.MEDICAL_RECORD,
    locale="ES",
    pattern=re.compile(r"\b(?:NHC|nhc)[\s:-]?\d{6,10}\b"),
    confidence=0.85,
    context_words=("historia", "clínica", "paciente"),
    description="Spanish medical record number (NHC)",
)


# =============================================================================
# US PATTERNS (EN-US)
# =============================================================================

US_SSN = EntityPattern(
    entity_type=ET.SSN,
    locale="US",
    pattern=re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    confidence=1.0,
    context_words=("ssn", "social security"),
    description="US Social Security Number",
)

US_PHONE = EntityPattern(
    entity_type=ET.PHONE_NUMBER,
    locale="US",
    pattern=re.compile(r"\b(?:\+1\s?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    confidence=0.9,
    description="US phone numbers",
)

US_ZIP_CODE = EntityPattern(
    entity_type=ET.POSTAL_CODE,
    locale="US",
    pattern=re.compile(r"\b\d{5}(?:-\d{4})?\b"),
    confidence=0.7,
    context_words=("zip", "code"),
    description="US ZIP code",
)

US_DRIVERS_LICENSE = EntityPattern(
    entity_type=ET.DRIVERS_LICENSE,
    locale="US",
    pattern=re.compile(r"\b[A-Z]\d{7}\b"),
    confidence=0.6,
    context_words=("license", "driver", "dl"),
    description="US driver's license (format varies by state)",
)

US_PASSPORT = EntityPattern(
    entity_type=ET.PASSPORT,
    locale="US",
    pattern=re.compile(r"\b[A-Z]\d{8}\b"),
    confidence=0.7,
    context_words=("passport", "travel"),
    description="US passport number",
)

US_AGE = EntityPattern(
    entity_type=ET.AGE,
    locale="US",
    pattern=re.compile(r"\b(\d{1,3})\s*(?:years?\s+old|y\.?o\.?)\b", re.IGNORECASE),
    confidence=0.9,
    description="Age in English",
)

US_MEDICAL_RECORD = EntityPattern(
    entity_type=ET.MEDICAL_RECORD,
    locale="US",
    pattern=re.compile(r"\b(?:MRN|mrn)[\s:-]?\d{6,10}\b"),
    confidence=0.85,
    context_words=("medical", "record", "patient"),
    description="US medical record number",
)


# =============================================================================
# FRENCH PATTERNS (FR)
# =============================================================================

FR_INSEE = EntityPattern(
    entity_type=ET.NATIONAL_ID,
    locale="FR",
    pattern=re.compile(r"\b[12]\d{12}\b"),
    confidence=0.95,
    context_words=("numéro de sécurité sociale", "nir", "insee"),
    description="French INSEE number (Sécurité Sociale)",
)

FR_PHONE = EntityPattern(
    entity_type=ET.PHONE_NUMBER,
    locale="FR",
    pattern=re.compile(r"(?:\+33\s?)?[1-9](?:\s?\d{2}){4}\b"),
    confidence=0.9,
    description="French phone numbers",
)

FR_POSTAL_CODE = EntityPattern(
    entity_type=ET.POSTAL_CODE,
    locale="FR",
    pattern=re.compile(r"\b\d{5}\b"),
    confidence=0.6,
    context_words=("code postal", "cp"),
    description="French postal code",
)

FR_IBAN = EntityPattern(
    entity_type=ET.IBAN,
    locale="FR",
    pattern=re.compile(r"\bFR\d{2}\s?\d{5}\s?\d{5}\s?\d{11}\s?\d{2}\b"),
    confidence=0.95,
    context_words=("iban", "compte", "bancaire"),
    description="French IBAN",
)


# =============================================================================
# GERMAN PATTERNS (DE)
# =============================================================================

DE_TAX_ID = EntityPattern(
    entity_type=ET.TAX_ID,
    locale="DE",
    pattern=re.compile(r"\b\d{11}\b"),
    confidence=0.7,
    context_words=("steuer", "identifikationsnummer", "steuernummer"),
    description="German tax ID (Steueridentifikationsnummer)",
)

DE_PHONE = EntityPattern(
    entity_type=ET.PHONE_NUMBER,
    locale="DE",
    pattern=re.compile(r"\b(?:\+49\s?)?(?:\(0\)\s?)?\d{2,5}[-\s]?\d{3,10}\b"),
    confidence=0.8,
    description="German phone numbers",
)

DE_POSTAL_CODE = EntityPattern(
    entity_type=ET.POSTAL_CODE,
    locale="DE",
    pattern=re.compile(r"\b\d{5}\b"),
    confidence=0.6,
    context_words=("plz", "postleitzahl"),
    description="German postal code",
)

DE_IBAN = EntityPattern(
    entity_type=ET.IBAN,
    locale="DE",
    pattern=re.compile(r"\bDE\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}\b"),
    confidence=0.95,
    context_words=("iban", "konto"),
    description="German IBAN",
)


# =============================================================================
# ITALIAN PATTERNS (IT)
# =============================================================================

IT_FISCAL_CODE = EntityPattern(
    entity_type=ET.NATIONAL_ID,
    locale="IT",
    pattern=re.compile(r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b"),
    confidence=0.95,
    context_words=("codice fiscale"),
    description="Italian fiscal code (Codice Fiscale)",
)

IT_PHONE = EntityPattern(
    entity_type=ET.PHONE_NUMBER,
    locale="IT",
    pattern=re.compile(r"\b(?:\+39\s?)?3\d{9}\b"),
    confidence=0.9,
    description="Italian mobile phone numbers",
)

IT_POSTAL_CODE = EntityPattern(
    entity_type=ET.POSTAL_CODE,
    locale="IT",
    pattern=re.compile(r"\b\d{5}\b"),
    confidence=0.6,
    context_words=("cap", "codice postale"),
    description="Italian postal code",
)

IT_IBAN = EntityPattern(
    entity_type=ET.IBAN,
    locale="IT",
    pattern=re.compile(r"\bIT\d{2}\s?[A-Z]\s?\d{5}\s?\d{5}\s?\d{12}\b"),
    confidence=0.95,
    context_words=("iban", "conto"),
    description="Italian IBAN",
)


# =============================================================================
# PORTUGUESE PATTERNS (PT)
# =============================================================================

PT_NIF = EntityPattern(
    entity_type=ET.TAX_ID,
    locale="PT",
    pattern=re.compile(r"\b\d{9}\b"),
    confidence=0.7,
    context_words=("nif", "número de identificação fiscal"),
    description="Portuguese tax ID (NIF)",
)

PT_PHONE = EntityPattern(
    entity_type=ET.PHONE_NUMBER,
    locale="PT",
    pattern=re.compile(r"\b(?:\+351\s?)?[29]\d{8}\b"),
    confidence=0.9,
    description="Portuguese phone numbers",
)

PT_POSTAL_CODE = EntityPattern(
    entity_type=ET.POSTAL_CODE,
    locale="PT",
    pattern=re.compile(r"\b\d{4}-\d{3}\b"),
    confidence=0.8,
    description="Portuguese postal code",
)

PT_IBAN = EntityPattern(
    entity_type=ET.IBAN,
    locale="PT",
    pattern=re.compile(r"\bPT\d{2}\s?\d{4}\s?\d{4}\s?\d{11}\s?\d{2}\b"),
    confidence=0.95,
    context_words=("iban", "conta"),
    description="Portuguese IBAN",
)


# =============================================================================
# MASTER PATTERN LIST
# =============================================================================

LOCALE_PATTERNS: list[EntityPattern] = [
    # Global
    GLOBAL_EMAIL,
    GLOBAL_IP_V4,
    GLOBAL_IP_V6,
    GLOBAL_CREDIT_CARD,
    
    # Spanish (ES)
    ES_DNI,
    ES_NIE,
    ES_PHONE_MOBILE,
    ES_PHONE_LANDLINE,
    ES_SOCIAL_SECURITY,
    ES_IBAN,
    ES_POSTAL_CODE,
    ES_LICENSE_PLATE,
    ES_AGE,
    ES_MEDICAL_RECORD,
    
    # US
    US_SSN,
    US_PHONE,
    US_ZIP_CODE,
    US_DRIVERS_LICENSE,
    US_PASSPORT,
    US_AGE,
    US_MEDICAL_RECORD,
    
    # French (FR)
    FR_INSEE,
    FR_PHONE,
    FR_POSTAL_CODE,
    FR_IBAN,
    
    # German (DE)
    DE_TAX_ID,
    DE_PHONE,
    DE_POSTAL_CODE,
    DE_IBAN,
    
    # Italian (IT)
    IT_FISCAL_CODE,
    IT_PHONE,
    IT_POSTAL_CODE,
    IT_IBAN,
    
    # Portuguese (PT)
    PT_NIF,
    PT_PHONE,
    PT_POSTAL_CODE,
    PT_IBAN,
]
