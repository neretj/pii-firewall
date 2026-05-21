"""Spanish (Spain) locale patterns."""

import re
from ..catalog import EntityPattern
from ... import entity_types as ET


# =============================================================================
# NATIONAL ID
# =============================================================================

ES_DNI = EntityPattern(
    entity_type=ET.NATIONAL_ID,
    locale="ES",
    pattern=re.compile(r"\b\d{8}[A-Z]\b"),
    confidence=1.0,
    context_words=("dni", "documento", "identidad", "nacional"),
    description="Spanish DNI (Documento Nacional de Identidad)",
)

ES_NIE = EntityPattern(
    entity_type=ET.NATIONAL_ID,
    locale="ES",
    pattern=re.compile(r"\b[XYZ]\d{7}[A-Z]\b"),
    confidence=1.0,
    context_words=("nie", "extranjero", "identificación"),
    description="Spanish NIE (Número de Identificación de Extranjero)",
)


# =============================================================================
# PHONE NUMBERS
# =============================================================================

ES_PHONE_MOBILE = EntityPattern(
    entity_type=ET.PHONE_NUMBER,
    locale="ES",
    pattern=re.compile(r"(?<!\w)(?:\+34\s?)?[67]\d{8}\b"),
    confidence=1.0,
    description="Spanish mobile phone numbers (6xx/7xx)",
)

ES_PHONE_LANDLINE = EntityPattern(
    entity_type=ET.PHONE_NUMBER,
    locale="ES",
    pattern=re.compile(r"(?<!\w)(?:\+34\s?)?[89]\d{8}\b"),
    confidence=1.0,
    description="Spanish landline phone numbers (8xx/9xx)",
)


# =============================================================================
# SOCIAL SECURITY
# =============================================================================

ES_SOCIAL_SECURITY = EntityPattern(
    entity_type=ET.SSN,
    locale="ES",
    pattern=re.compile(r"\b\d{12}\b"),
    confidence=0.7,
    context_words=("seguridad social", "ss", "nass", "afiliación"),
    description="Spanish Social Security Number (12 digits)",
)


# =============================================================================
# BANKING
# =============================================================================

ES_IBAN = EntityPattern(
    entity_type=ET.IBAN,
    locale="ES",
    pattern=re.compile(r"\bES\d{2}\s?\d{4}\s?\d{4}\s?\d{2}\s?\d{10}\b"),
    confidence=0.95,
    context_words=("iban", "cuenta", "bancaria", "banco"),
    description="Spanish IBAN (ES + 22 digits)",
)


# =============================================================================
# ADDRESS
# =============================================================================

ES_POSTAL_CODE = EntityPattern(
    entity_type=ET.POSTAL_CODE,
    locale="ES",
    pattern=re.compile(r"\b\d{5}\b"),
    confidence=0.6,
    context_words=("cp", "código postal", "c.p.", "postal"),
    description="Spanish postal code (5 digits)",
)


# =============================================================================
# VEHICLE
# =============================================================================

ES_LICENSE_PLATE = EntityPattern(
    entity_type=ET.LICENSE_PLATE,
    locale="ES",
    pattern=re.compile(r"\b\d{4}\s?[A-Z]{3}\b"),
    confidence=0.8,
    context_words=("matrícula", "coche", "vehículo", "automóvil"),
    description="Spanish vehicle license plate (4 digits + 3 letters)",
)


# =============================================================================
# AGE
# =============================================================================

ES_AGE = EntityPattern(
    entity_type=ET.AGE,
    locale="ES",
    pattern=re.compile(r"\b\d{1,3}\s*años?\b", re.IGNORECASE),
    confidence=0.9,
    description="Age in Spanish (años)",
)


# =============================================================================
# MEDICAL
# =============================================================================

ES_MEDICAL_RECORD = EntityPattern(
    entity_type=ET.MEDICAL_RECORD,
    locale="ES",
    pattern=re.compile(r"\b(?:NHC|nhc)[\s:-]?\d{6,10}\b"),
    confidence=0.85,
    context_words=("historia", "clínica", "paciente", "nhc"),
    description="Spanish medical record number (NHC - Número de Historia Clínica)",
)


# =============================================================================
# PASSPORT
# =============================================================================

ES_PASSPORT = EntityPattern(
    entity_type=ET.PASSPORT,
    locale="ES",
    pattern=re.compile(r"\b[A-Z]{3}\d{6}\b"),
    confidence=0.75,
    context_words=("pasaporte", "passport", "viaje"),
    description="Spanish passport number",
)


# =============================================================================
# EXPORT
# =============================================================================

ES_PATTERNS = [
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
    ES_PASSPORT,
]
