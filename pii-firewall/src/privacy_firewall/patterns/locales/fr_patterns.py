"""French locale patterns."""

import re
from ..catalog import EntityPattern


# =============================================================================
# NATIONAL ID / SOCIAL SECURITY
# =============================================================================

FR_INSEE = EntityPattern(
    entity_type="NATIONAL_ID",
    locale="FR",
    pattern=re.compile(r"\b[12]\d{2}[01]\d[0-9AB]\d{8}\b"),
    confidence=0.95,
    context_words=("numéro de sécurité sociale", "nir", "insee", "sécurité sociale"),
    description="French INSEE number (Numéro de Sécurité Sociale)",
)


# =============================================================================
# PHONE NUMBERS
# =============================================================================

FR_PHONE = EntityPattern(
    entity_type="PHONE",
    locale="FR",
    pattern=re.compile(r"\b(?:\+33\s?)?[1-9](?:\s?\d{2}){4}\b"),
    confidence=0.9,
    description="French phone numbers (10 digits)",
)


# =============================================================================
# ADDRESS
# =============================================================================

FR_POSTAL_CODE = EntityPattern(
    entity_type="POSTAL_CODE",
    locale="FR",
    pattern=re.compile(r"\b\d{5}\b"),
    confidence=0.6,
    context_words=("code postal", "cp", "postal"),
    description="French postal code (5 digits)",
)


# =============================================================================
# BANKING
# =============================================================================

FR_IBAN = EntityPattern(
    entity_type="IBAN",
    locale="FR",
    pattern=re.compile(r"\bFR\d{2}\s?\d{5}\s?\d{5}\s?\d{11}\s?\d{2}\b"),
    confidence=0.95,
    context_words=("iban", "compte", "bancaire", "banque"),
    description="French IBAN (FR + 25 digits)",
)


# =============================================================================
# PASSPORT
# =============================================================================

FR_PASSPORT = EntityPattern(
    entity_type="PASSPORT",
    locale="FR",
    pattern=re.compile(r"\b\d{2}[A-Z]{2}\d{5}\b"),
    confidence=0.75,
    context_words=("passeport", "passport"),
    description="French passport number",
)


# =============================================================================
# EXPORT
# =============================================================================

FR_PATTERNS = [
    FR_INSEE,
    FR_PHONE,
    FR_POSTAL_CODE,
    FR_IBAN,
    FR_PASSPORT,
]
