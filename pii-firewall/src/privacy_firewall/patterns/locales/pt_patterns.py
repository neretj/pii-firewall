"""Portuguese locale patterns."""

import re
from ..catalog import EntityPattern


# =============================================================================
# TAX ID
# =============================================================================

PT_NIF = EntityPattern(
    entity_type="TAX_ID",
    locale="PT",
    pattern=re.compile(r"\b\d{9}\b"),
    confidence=0.7,
    context_words=("nif", "número de identificação fiscal", "contribuinte"),
    description="Portuguese tax ID (NIF - 9 digits)",
)

PT_CPF = EntityPattern(
    entity_type="TAX_ID",
    locale="PT",
    pattern=re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
    confidence=0.95,
    context_words=("cpf", "cadastro", "fiscal"),
    description="Brazilian CPF format used in Portuguese prompts",
)


# =============================================================================
# PHONE NUMBERS
# =============================================================================

PT_PHONE = EntityPattern(
    entity_type="PHONE",
    locale="PT",
    pattern=re.compile(r"\b(?:\+351\s?)?[29]\d{8}\b"),
    confidence=0.9,
    description="Portuguese phone numbers (9 digits)",
)

PT_BR_PHONE = EntityPattern(
    entity_type="PHONE",
    locale="PT",
    pattern=re.compile(r"(?<!\w)(?:\+55\s?)?(?:\d{2}\s?)?9?\d{8,9}\b"),
    confidence=0.85,
    context_words=("telefone", "celular", "contato"),
    description="Brazilian phone numbers used in Portuguese prompts",
)


# =============================================================================
# ADDRESS
# =============================================================================

PT_POSTAL_CODE = EntityPattern(
    entity_type="POSTAL_CODE",
    locale="PT",
    pattern=re.compile(r"\b\d{4}-\d{3}\b"),
    confidence=0.8,
    context_words=("código postal", "cp", "postal"),
    description="Portuguese postal code (XXXX-XXX)",
)


# =============================================================================
# BANKING
# =============================================================================

PT_IBAN = EntityPattern(
    entity_type="IBAN",
    locale="PT",
    pattern=re.compile(r"\bPT\d{2}\s?\d{4}\s?\d{4}\s?\d{11}\s?\d{2}\b"),
    confidence=0.95,
    context_words=("iban", "conta", "bancária", "banco"),
    description="Portuguese IBAN (PT + 23 digits)",
)

PT_ACCOUNT = EntityPattern(
    entity_type="ACCOUNT_NUMBER",
    locale="PT",
    pattern=re.compile(r"\b\d{5}-\d\s\d{5}-\d\b"),
    confidence=0.85,
    context_words=("conta", "banco", "agência"),
    description="Brazilian account style (12345-6 78901-2)",
)


# =============================================================================
# EXPORT
# =============================================================================

PT_PATTERNS = [
    PT_NIF,
    PT_CPF,
    PT_PHONE,
    PT_BR_PHONE,
    PT_POSTAL_CODE,
    PT_IBAN,
    PT_ACCOUNT,
]
