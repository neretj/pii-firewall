"""Universal pattern recognizers that work across all languages.

These recognizers detect entities using patterns that are language-agnostic.
They work for ANY language: English, Spanish, French, German, etc.

Includes:
- International phone numbers with country code (+34, +33, +1, +49, etc.)
- Numeric date formats (DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY, MM/DD/YYYY)
- Abbreviated names (A. Garcia, Ana G., J. Smith)

Architecture:
- Each recognizer requires a `supported_language` parameter (Presidio requirement)
- Patterns themselves are universal - same regex works for all languages
- Context words include multiple languages to improve detection
"""

from presidio_analyzer import Pattern, PatternRecognizer
from typing import List


def create_universal_phone_recognizer(language: str) -> PatternRecognizer:
    """Universal international phone number recognizer.
    
    Detects phone numbers with international prefix (+XX...).
    Works for: +34 (ES), +33 (FR), +1 (US), +49 (DE), +39 (IT), +55 (BR), etc.
    
    Pattern coverage:
    - +34612345678 (Spanish mobile)
    - +33 6 12 34 56 78 (French mobile)
    - +1-555-123-4567 (US with dashes)
    - (555) 123-4567 (US local format)
    
    Args:
        language: Language code (required by Presidio even though pattern is universal)
    
    Returns:
        PatternRecognizer for international phone numbers
    """
    patterns = [
        Pattern(
            name="international_phone",
            regex=r"\+\d{1,3}\s?\d{9,10}\b",  # +XX XXXXXXXXX
            score=0.95,
        ),
        Pattern(
            name="international_phone_with_spaces",
            regex=r"\+\d{1,3}\s?\d{3}\s?\d{3}\s?\d{3,4}\b",  # +XX XXX XXX XXX
            score=0.90,
        ),
        Pattern(
            name="us_phone_format",
            regex=r"\+?1?\s?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}\b",  # (555) 123-4567
            score=0.85,
        ),
    ]
    
    return PatternRecognizer(
        supported_entity="PHONE_NUMBER",
        patterns=patterns,
        context=["phone", "tel", "teléfono", "téléphone", "telefono", "móvil", "mobile", "celular", "contact"],
        supported_language=language,
    )


def create_universal_date_recognizer(language: str) -> PatternRecognizer:
    """Universal numeric date pattern recognizer.
    
    Detects common numeric date formats that work across all languages:
    - DD/MM/YYYY (European: 15/03/1980)
    - DD-MM-YYYY (European with dashes: 15-03-1980)
    - YYYY-MM-DD (ISO format: 1980-03-15)
    - MM/DD/YYYY (US format: 03/15/1980)
    
    Note: Language-specific textual dates (e.g., "15 de marzo de 1980") 
    are handled in language-specific recognizers.
    
    Args:
        language: Language code (required by Presidio)
    
    Returns:
        PatternRecognizer for numeric date formats
    """
    patterns = [
        Pattern(
            name="date_iso",
            regex=r"\b\d{4}-(0?[1-9]|1[0-2])-(0?[1-9]|[12][0-9]|3[01])\b",
            score=0.95,
        ),  # YYYY-MM-DD (unambiguous ISO format)
        Pattern(
            name="date_slash_dmy",
            regex=r"\b(0?[1-9]|[12][0-9]|3[01])/(0?[1-9]|1[0-2])/\d{4}\b",
            score=0.85,
        ),  # DD/MM/YYYY (European)
        Pattern(
            name="date_dash_dmy",
            regex=r"\b(0?[1-9]|[12][0-9]|3[01])-(0?[1-9]|1[0-2])-\d{4}\b",
            score=0.85,
        ),  # DD-MM-YYYY (European)
        Pattern(
            name="date_slash_mdy",
            regex=r"\b(0?[1-9]|1[0-2])/(0?[1-9]|[12][0-9]|3[01])/\d{4}\b",
            score=0.75,  # Lower score due to ambiguity with DD/MM/YYYY
        ),  # MM/DD/YYYY (US)
    ]
    
    return PatternRecognizer(
        supported_entity="DATE_TIME",
        patterns=patterns,
        context=["date", "fecha", "born", "birthday", "naissance", "né", "nacido", "birth", "dob"],
        supported_language=language,
    )


def create_universal_abbreviated_name_recognizer(language: str) -> PatternRecognizer:
    """Universal abbreviated name recognizer.
    
    Detects names with abbreviated parts across all languages:
    - "Ana G." (first name + initial)
    - "A. Garcia" (initial + last name)
    - "Ana B. Garcia" (first + middle initial + last)
    - "J. Smith" (English)
    - "M. Dupont" (French)
    
    Pattern is universal: uses capital letters and periods.
    Works for: Spanish, English, French, German, Italian, Portuguese, etc.
    
    Args:
        language: Language code (required by Presidio)
    
    Returns:
        PatternRecognizer for abbreviated names
    """
    patterns = [
        Pattern(
            name="first_last_abbreviated",
            regex=r'\b[A-Z][a-z]+\s+[A-Z]\.',
            score=0.95,  # High score to override SpacyRecognizer's incorrect boundaries
        ),  # "Ana G.", "John D."
        Pattern(
            name="abbreviated_first_last",
            regex=r'\b[A-Z]\.\s+[A-Z][a-z]+\b',
            score=0.95,
        ),  # "A. Garcia", "J. Smith"
        Pattern(
            name="first_middle_last_abbreviated",
            regex=r'\b[A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+\b',
            score=0.95,
        ),  # "Ana B. Garcia"
        Pattern(
            name="abbreviated_middle_last",
            regex=r'\b[A-Z]\.\s+[A-Z]\.\s+[A-Z][a-z]+\b',
            score=0.95,
        ),  # "A. B. Garcia"
    ]
    
    return PatternRecognizer(
        supported_entity="PERSON",
        patterns=patterns,
        context=["name", "patient", "client", "returned", "visited", "Dr", "Mr", "Mrs", "Ms", "nombre", "nom"],
        supported_language=language,
    )


def create_universal_recognizers(language: str) -> List[PatternRecognizer]:
    """Create all universal recognizers for a given language.
    
    These recognizers work for ANY language using language-agnostic patterns.
    
    Args:
        language: Language code (en, es, fr, de, it, pt, etc.)
    
    Returns:
        List of universal PatternRecognizers:
        - Phone numbers (international format)
        - Dates (numeric formats)
        - Abbreviated names
    """
    return [
        create_universal_phone_recognizer(language),
        create_universal_date_recognizer(language),
        create_universal_abbreviated_name_recognizer(language),
    ]
