"""Spanish-specific pattern recognizers for Presidio.

These recognizers detect entities using patterns that are SPECIFIC to Spain/Spanish.
They complement universal recognizers with Spain-specific patterns.

Includes:
- DNI/NIF (Spanish national ID: 8 digits + letter)
- IBAN (Spanish bank accounts: ES + 22 digits)
- National phone numbers WITHOUT country code (6XX, 8XX, 9XX)
- Spanish date formats with month names ("15 de marzo de 1980")
- Common Spanish names (to correct spaCy misclassification as LOCATION)

Architecture:
- All recognizers have supported_language="es"
- Patterns specific to Spanish language/format conventions
- International formats (+34...) are handled by universal_recognizers.py
"""

from presidio_analyzer import Pattern, PatternRecognizer
from typing import List


def create_spanish_dni_recognizer() -> PatternRecognizer:
    """Spanish DNI/NIF pattern: 8 digits + letter.
    
    DNI (Documento Nacional de Identidad) is Spain-specific.
    Format: 12345678A (8 digits + control letter)
    Valid letters: all except I, O, U (easily confused with digits 1, 0)
    
    High score (0.99) to override potential DATE_TIME misdetection.
    
    Returns:
        PatternRecognizer for Spanish DNI/NIF
    """
    patterns = [
        Pattern(
            name="dni_standard",
            regex=r"\b\d{8}[A-HJ-NP-TV-Z]\b",  # 8 digits + valid letter
            score=0.99,  # Override DATE_TIME
        ),
        Pattern(
            name="dni_with_hyphen",
            regex=r"\b\d{8}-[A-HJ-NP-TV-Z]\b",
            score=0.99,
        ),
        Pattern(
            name="dni_with_spaces",
            regex=r"\b\d{2}\s?\d{3}\s?\d{3}\s?[A-HJ-NP-TV-Z]\b",
            score=0.95,
        ),
    ]
    
    return PatternRecognizer(
        supported_entity="NATIONAL_ID",  # Use standard entity type for consistency
        patterns=patterns,
        context=["DNI", "NIF", "ID", "identificación", "documento"],
        supported_language="es",
    )


def create_iban_recognizer() -> PatternRecognizer:
    """IBAN pattern - Spanish and general European.
    
    Spanish IBAN: ES + 22 digits
    General IBAN: 2 letters + 20-32 digits (ISO 13616)
    
    Note: While IBAN is European, we include it here since it's commonly
    used in Spanish contexts. Can be moved to a european_recognizers.py later.
    
    Returns:
        PatternRecognizer for IBAN bank accounts
    """
    patterns = [
        Pattern(
            name="iban_spanish",
            regex=r"\bES\d{22}\b",
            score=0.95,
        ),
        Pattern(
            name="iban_with_spaces_spanish",
            regex=r"\bES\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b",
            score=0.95,
        ),
        Pattern(
            name="iban_general",
            regex=r"\b[A-Z]{2}\d{2}[A-Z0-9]{12,30}\b",  # ISO 13616
            score=0.85,
        ),
    ]
    
    return PatternRecognizer(
        supported_entity="IBAN",
        patterns=patterns,
        context=["IBAN", "cuenta", "account", "bank", "banco"],
        supported_language="es",
    )


def create_spanish_national_phone_recognizer() -> PatternRecognizer:
    """Spanish national phone numbers WITHOUT international prefix.
    
    Detects Spanish phones in national format (no +34):
    - Mobile: 6XX XXX XXX or 7XX XXX XXX (starts with 6 or 7)
    - Landline: 8XX XXX XXX or 9XX XXX XXX (starts with 8 or 9)
    
    Note: International format (+34...) is handled by universal phone recognizer.
    This recognizer only catches national format calls within Spain.
    
    Lower scores (0.75-0.80) to avoid false positives with other numeric sequences.
    
    Returns:
        PatternRecognizer for Spanish national phone numbers
    """
    patterns = [
        Pattern(
            name="spanish_mobile_national",
            regex=r"\b[67]\d{2}\s?\d{3}\s?\d{3}\b",
            score=0.80,
        ),
        Pattern(
            name="spanish_landline_national",
            regex=r"\b[89]\d{2}\s?\d{3}\s?\d{3}\b",
            score=0.75,
        ),
    ]
    
    return PatternRecognizer(
        supported_entity="PHONE_NUMBER",
        patterns=patterns,
        context=["teléfono", "phone", "móvil", "celular", "llamar", "contacto"],
        supported_language="es",
    )


def create_spanish_date_recognizer() -> PatternRecognizer:
    """Spanish textual date patterns with month names.
    
    Detects dates written with Spanish month names:
    - "15 de marzo de 1980" (full format with "de")
    - "15 marzo 1980" (short format without "de")
    
    Numeric dates (15/03/1980) are handled by universal recognizers.
    
    Returns:
        PatternRecognizer for Spanish textual dates
    """
    spanish_months = "enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre"
    
    patterns = [
        Pattern(
            name="date_spanish_long",
            regex=rf'\b\d{{1,2}}\s+de\s+(?:{spanish_months})\s+de\s+\d{{4}}\b',
            score=0.95,
        ),  # "15 de marzo de 1980"
        Pattern(
            name="date_spanish_short",
            regex=rf'\b\d{{1,2}}\s+(?:{spanish_months})\s+\d{{4}}\b',
            score=0.90,
        ),  # "15 marzo 1980"
    ]
    
    return PatternRecognizer(
        supported_entity="DATE_TIME",
        patterns=patterns,
        context=["nacido", "nacida", "fecha", "nacimiento", "born", "birthday"],
        supported_language="es",
    )


def create_spanish_name_recognizer() -> PatternRecognizer:
    """Spanish name patterns to override LOCATION misclassification.
    
    Common Spanish names that spaCy en_core_web_sm may incorrectly classify as LOCATION.
    Examples: "García", "Martínez" may be tagged as GPE (geo-political entity)
    
    High score (0.85-0.90) to override NER but lower than specific pattern recognizers.
    
    Returns:
        PatternRecognizer for common Spanish names
    """
    patterns = [
        Pattern(
            name="spanish_female_full_name",
            regex=r"\b(?:María|Sofía|Carmen|Ana|Isabel|Lucía|Elena|Rosa|Teresa|Pilar)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\b",
            score=0.90,
        ),
        Pattern(
            name="spanish_male_full_name",
            regex=r"\b(?:José|Juan|Antonio|Manuel|Francisco|Pedro|Luis|Carlos|Miguel|Javier)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\b",
            score=0.90,
        ),
        Pattern(
            name="spanish_compound_surname",
            regex=r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+(?:García|Rodríguez|López|Martínez|Fernández|González|Pérez|Sánchez)\b",
            score=0.85,
        ),
    ]
    
    return PatternRecognizer(
        supported_entity="PERSON",
        patterns=patterns,
        supported_language="es",
    )


def create_spanish_recognizers() -> List[PatternRecognizer]:
    """Create all Spanish-specific recognizers.
    
    Returns:
        List of PatternRecognizer instances for Spanish-specific entities:
        - DNI (national ID)
        - IBAN (bank accounts)
        - National phone numbers (no +34)
        - Textual dates (with month names)
        - Common Spanish names
    """
    return [
        create_spanish_dni_recognizer(),
        create_iban_recognizer(),
        create_spanish_national_phone_recognizer(),
        create_spanish_date_recognizer(),
        create_spanish_name_recognizer(),
    ]
