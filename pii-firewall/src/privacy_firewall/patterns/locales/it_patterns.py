"""Italian locale patterns."""

import re
from ..catalog import EntityPattern


# =============================================================================
# NATIONAL ID
# =============================================================================

IT_FISCAL_CODE = EntityPattern(
    entity_type="NATIONAL_ID",
    locale="IT",
    pattern=re.compile(r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b"),
    confidence=0.95,
    context_words=("codice fiscale", "cf", "fiscal code"),
    description="Italian fiscal code (Codice Fiscale)",
)


# =============================================================================
# PHONE NUMBERS
# =============================================================================

IT_PHONE = EntityPattern(
    entity_type="PHONE",
    locale="IT",
    pattern=re.compile(r"(?:\+39\s?)?3\d{9}\b"),
    confidence=0.9,
    description="Italian mobile phone numbers",
)


# =============================================================================
# ADDRESS
# =============================================================================

IT_POSTAL_CODE = EntityPattern(
    entity_type="POSTAL_CODE",
    locale="IT",
    pattern=re.compile(r"\b\d{5}\b"),
    confidence=0.6,
    context_words=("cap", "codice postale", "postal"),
    description="Italian postal code (CAP - 5 digits)",
)


# =============================================================================
# BANKING
# =============================================================================

IT_IBAN = EntityPattern(
    entity_type="IBAN",
    locale="IT",
    pattern=re.compile(r"\bIT\d{2}\s?[A-Z]\s?\d{5}\s?\d{5}\s?\d{12}\b"),
    confidence=0.95,
    context_words=("iban", "conto", "bancario", "banca"),
    description="Italian IBAN (IT + check digits + 23 chars)",
)


# =============================================================================
# VAT
# =============================================================================

IT_VAT = EntityPattern(
    entity_type="TAX_ID",
    locale="IT",
    pattern=re.compile(r"\b\d{11}\b"),
    confidence=0.7,
    context_words=("partita iva", "p.iva", "vat", "iva"),
    description="Italian VAT number (Partita IVA - 11 digits)",
)


# =============================================================================
# EXPORT
# =============================================================================

IT_PATTERNS = [
    IT_FISCAL_CODE,
    IT_PHONE,
    IT_POSTAL_CODE,
    IT_IBAN,
    IT_VAT,
]
