"""Orchestrator for combining all recognizers (universal + language-specific).

This module is the ORCHESTRATOR that builds the complete list of recognizers
for a given language by combining:
1. Universal recognizers (work for all languages)
2. Language-specific recognizers (Spanish, French, etc.)

Architecture:
- universal_recognizers.py: Patterns that work for ALL languages
  - Phone numbers (+34, +33, +1, etc.)
  - Numeric dates (DD/MM/YYYY, YYYY-MM-DD, etc.)
  - Abbreviated names (A. Garcia, Ana G.)

- spanish_recognizers.py: Patterns SPECIFIC to Spanish
  - DNI (national ID)
  - IBAN (bank accounts)
  - National phones (6XX, 8XX, 9XX without +34)
  - Textual dates ("15 de marzo de 1980")
  - Common Spanish names

- [Future] french_recognizers.py: French-specific patterns
  - INSEE number
  - French dates ("15 mars 1980")
  
- [Future] german_recognizers.py: German-specific patterns
  - Personalausweis
  - German dates ("15. März 1980")

This module's role: Import and combine recognizers from all sources.
"""

from __future__ import annotations

from typing import Any


def create_enhanced_recognizers(language: str = "en") -> list[Any]:
    """Create all recognizers for a given language.
    
    Combines universal recognizers (work for all languages) with
    language-specific recognizers for the target language.
    
    Args:
        language: Language code (en, es, fr, de, it, pt, etc.)
    
    Returns:
        Complete list of PatternRecognizers:
        - Universal recognizers (phone, date, abbreviated names)
        - Language-specific recognizers (DNI, INSEE, etc.)
    
    Example:
        For Spanish (es):
        - Universal: +34..., DD/MM/YYYY, Ana G.
        - Spanish-specific: DNI, IBAN, 6XX XXX XXX, "15 de marzo de 1980"
        
        For French (fr):
        - Universal: +33..., DD/MM/YYYY, M. Dupont
        - French-specific: INSEE, "15 mars 1980" (when implemented)
    """
    recognizers = []

    try:
        from .universal_recognizers import create_universal_recognizers
        recognizers.extend(create_universal_recognizers(language))
    except ImportError:
        pass

    if language == "es":
        try:
            from .spanish_recognizers import create_spanish_recognizers
            recognizers.extend(create_spanish_recognizers())
        except ImportError:
            pass

    return recognizers
