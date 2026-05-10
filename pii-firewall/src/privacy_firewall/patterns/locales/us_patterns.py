"""United States (English) locale patterns."""

import re
from ..catalog import EntityPattern


# =============================================================================
# SOCIAL SECURITY NUMBER
# =============================================================================

US_SSN = EntityPattern(
    entity_type="SSN",
    locale="US",
    pattern=re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    confidence=1.0,
    context_words=("ssn", "social security", "social security number"),
    description="US Social Security Number (XXX-XX-XXXX)",
)

US_SSN_NO_DASH = EntityPattern(
    entity_type="SSN",
    locale="US",
    pattern=re.compile(r"\b\d{9}\b"),
    confidence=0.7,
    context_words=("ssn", "social security"),
    description="US Social Security Number without dashes",
)


# =============================================================================
# PHONE NUMBERS
# =============================================================================

US_PHONE = EntityPattern(
    entity_type="PHONE",
    locale="US",
    pattern=re.compile(r"\b(?:\+1\s?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    confidence=0.9,
    description="US phone numbers (various formats)",
)

US_PHONE_SHORT = EntityPattern(
    entity_type="PHONE",
    locale="US",
    pattern=re.compile(r"(?<!\w)(?:\+1[-.\s]?)?\d{3}[-.\s]?\d{4}\b"),
    confidence=0.8,
    context_words=("phone", "tel", "contact", "call"),
    description="US short local phone numbers (7 digits) with optional +1 prefix",
)


# =============================================================================
# ADDRESS
# =============================================================================

US_ZIP_CODE = EntityPattern(
    entity_type="POSTAL_CODE",
    locale="US",
    pattern=re.compile(r"\b\d{5}(?:-\d{4})?\b"),
    confidence=0.7,
    context_words=("zip", "code", "postal"),
    description="US ZIP code (5 or 9 digits)",
)


# =============================================================================
# IDENTIFICATION
# =============================================================================

US_DRIVERS_LICENSE = EntityPattern(
    entity_type="DRIVERS_LICENSE",
    locale="US",
    pattern=re.compile(r"\b[A-Z]\d{7,14}\b"),
    confidence=0.6,
    context_words=("license", "driver", "dl", "driver's license"),
    description="US driver's license (format varies by state)",
)

US_PASSPORT = EntityPattern(
    entity_type="PASSPORT",
    locale="US",
    pattern=re.compile(r"\b[0-9]{9}\b"),
    confidence=0.7,
    context_words=("passport", "travel", "passport number"),
    description="US passport number (9 digits)",
)


# =============================================================================
# AGE
# =============================================================================

US_AGE = EntityPattern(
    entity_type="AGE",
    locale="US",
    pattern=re.compile(r"\b(\d{1,3})\s*(?:years?\s+old|y\.?o\.?|yrs?\s+old)\b", re.IGNORECASE),
    confidence=0.9,
    description="Age in English (years old, y.o., etc.)",
)


# =============================================================================
# MEDICAL
# =============================================================================

US_MEDICAL_RECORD = EntityPattern(
    entity_type="MEDICAL_RECORD",
    locale="US",
    pattern=re.compile(r"\b(?:MRN|mrn)[\s:-]?\d{6,10}\b"),
    confidence=0.85,
    context_words=("medical", "record", "patient", "mrn"),
    description="US medical record number (MRN)",
)


# =============================================================================
# BANKING
# =============================================================================

US_ROUTING_NUMBER = EntityPattern(
    entity_type="ROUTING_NUMBER",
    locale="US",
    pattern=re.compile(r"\b\d{9}\b"),
    confidence=0.6,
    context_words=("routing", "routing number", "aba", "bank"),
    description="US bank routing number (9 digits)",
)

US_ACCOUNT_NUMBER = EntityPattern(
    entity_type="ACCOUNT_NUMBER",
    locale="US",
    pattern=re.compile(r"\b\d{8,17}\b"),
    confidence=0.5,
    context_words=("account", "account number", "checking", "savings"),
    description="US bank account number (8-17 digits)",
)


# =============================================================================
# TAX
# =============================================================================

US_EIN = EntityPattern(
    entity_type="TAX_ID",
    locale="US",
    pattern=re.compile(r"\b\d{2}-\d{7}\b"),
    confidence=0.9,
    context_words=("ein", "employer identification", "tax id", "federal tax"),
    description="US Employer Identification Number (EIN)",
)


# =============================================================================
# EXPORT
# =============================================================================

US_PATTERNS = [
    US_SSN,
    US_SSN_NO_DASH,
    US_PHONE,
    US_PHONE_SHORT,
    US_ZIP_CODE,
    US_DRIVERS_LICENSE,
    US_PASSPORT,
    US_AGE,
    US_MEDICAL_RECORD,
    US_ROUTING_NUMBER,
    US_ACCOUNT_NUMBER,
    US_EIN,
]
