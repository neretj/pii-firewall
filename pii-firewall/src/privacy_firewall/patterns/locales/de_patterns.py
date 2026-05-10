"""German locale patterns."""

import re
from ..catalog import EntityPattern


# =============================================================================
# TAX ID
# =============================================================================

DE_TAX_ID = EntityPattern(
    entity_type="TAX_ID",
    locale="DE",
    pattern=re.compile(r"\b\d{11}\b"),
    confidence=0.7,
    context_words=("steuer", "identifikationsnummer", "steuernummer", "steuer-id"),
    description="German tax ID (Steueridentifikationsnummer - 11 digits)",
)

DE_TAX_ID_PREFIXED = EntityPattern(
    entity_type="TAX_ID",
    locale="DE",
    pattern=re.compile(r"\bDE\d{9,11}\b"),
    confidence=0.9,
    context_words=("versicherung", "steuer", "id", "nummer"),
    description="German prefixed tax/insurance identifiers (DE + digits)",
)


# =============================================================================
# PHONE NUMBERS
# =============================================================================

DE_PHONE = EntityPattern(
    entity_type="PHONE",
    locale="DE",
    pattern=re.compile(r"\b(?:\+49\s?)?(?:\(0\)\s?)?\d{2,5}[-\s]?\d{3,10}\b"),
    confidence=0.8,
    description="German phone numbers",
)


# =============================================================================
# ADDRESS
# =============================================================================

DE_POSTAL_CODE = EntityPattern(
    entity_type="POSTAL_CODE",
    locale="DE",
    pattern=re.compile(r"\b\d{5}\b"),
    confidence=0.6,
    context_words=("plz", "postleitzahl", "postal"),
    description="German postal code (5 digits)",
)


# =============================================================================
# BANKING
# =============================================================================

DE_IBAN = EntityPattern(
    entity_type="IBAN",
    locale="DE",
    pattern=re.compile(r"\bDE\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}\b"),
    confidence=0.95,
    context_words=("iban", "konto", "bank", "bankverbindung"),
    description="German IBAN (DE + 20 digits)",
)


# =============================================================================
# DATES
# =============================================================================

DE_DATE_DOTTED = EntityPattern(
    entity_type="DATE_TIME",
    locale="DE",
    pattern=re.compile(r"\b(?:0?[1-9]|[12]\d|3[01])\.(?:0?[1-9]|1[0-2])\.\d{4}\b"),
    confidence=0.85,
    context_words=("geboren", "datum", "am"),
    description="German dotted date format (dd.mm.yyyy)",
)


# =============================================================================
# EXPORT
# =============================================================================

DE_PATTERNS = [
    DE_TAX_ID,
    DE_TAX_ID_PREFIXED,
    DE_PHONE,
    DE_POSTAL_CODE,
    DE_IBAN,
    DE_DATE_DOTTED,
]
