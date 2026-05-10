"""Custom Presidio recognizers for domain-specific entities.

This module provides:
- Factory for creating PatternRecognizer from catalog patterns
- Domain-specific recognizers (medical, financial, legal)
- Helper for user-defined custom recognizers
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PatternRecognizerFactory:
    """Factory for creating Presidio PatternRecognizer from catalog patterns."""
    
    @staticmethod
    def from_pattern(entity_pattern: Any, language: str = "en") -> Any:
        """Create Presidio PatternRecognizer from EntityPattern.
        
        Args:
            entity_pattern: EntityPattern instance from catalog
            language: Language code for the recognizer
        
        Returns:
            Presidio PatternRecognizer
        """
        try:
            from presidio_analyzer import Pattern, PatternRecognizer  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "Presidio not installed. Install with: pip install 'pii-firewall[presidio]'"
            ) from exc
        
        # Create Presidio Pattern from our EntityPattern
        pattern = Pattern(
            name=f"{entity_pattern.entity_type}_{entity_pattern.locale}",
            regex=entity_pattern.pattern.pattern,
            score=entity_pattern.confidence,
        )
        
        # Create PatternRecognizer with explicit language support
        recognizer = PatternRecognizer(
            supported_entity=entity_pattern.entity_type,
            patterns=[pattern],
            context=list(entity_pattern.context_words) if entity_pattern.context_words else None,
            supported_language=language,  # Explicitly set language
        )
        
        return recognizer
    
    @staticmethod
    def from_catalog(catalog: Any, locale: str, language: str = "en") -> list[Any]:
        """Create all Presidio recognizers for a locale from catalog.
        
        Args:
            catalog: PatternCatalog instance
            locale: Locale code (e.g., 'ES', 'US')
            language: Language code for the recognizers
        
        Returns:
            List of Presidio PatternRecognizers
        """
        patterns = catalog.get_all_patterns_for_locale(locale)
        
        recognizers = []
        for pattern in patterns:
            recognizer = PatternRecognizerFactory.from_pattern(pattern, language=language)
            recognizers.append(recognizer)
        
        return recognizers


class MedicalEntityRecognizer:
    """Recognizer for medical entities using domain-specific NER.
    
    This is a placeholder for integration with medical NER models like:
    - scispaCy (en_ner_bc5cdr_md for drugs and diseases)
    - MedSpaCy
    - BioBERT-based models
    - ClinicalBERT
    
    For now, it provides the structure for future integration.
    """
    
    def __init__(self, language: str = "en"):
        self.language = language
        self.supported_entities = [
            "DIAGNOSIS",
            "DRUG",
            "PROCEDURE",
            "LAB_VALUE",
            "VITAL_SIGN",
            "SYMPTOM",
            "ANATOMICAL_SITE",
        ]
    
    def load(self):
        """Load medical NER model.
        
        Future implementation:
        - For English: Load scispaCy en_ner_bc5cdr_md
        - For Spanish: Load Spanish medical NER model
        - For others: Use BioBERT fine-tuned on medical NER
        """
        # Placeholder for future implementation
        print(f"⚠ MedicalEntityRecognizer for {self.language} not yet implemented")
        print(f"  Supported entities: {', '.join(self.supported_entities)}")
        print(f"  Future: Will use scispaCy/BioBERT for medical NER")
    
    def analyze(self, text: str) -> list:
        """Analyze text for medical entities.
        
        Args:
            text: Clinical text
        
        Returns:
            List of medical entities (Presidio RecognizerResult format)
        """
        # Placeholder - would return actual medical entities
        return []


class FinancialEntityRecognizer:
    """Recognizer for financial entities.
    
    Detects:
    - Transaction amounts
    - Currency codes
    - Company names (via NER)
    - Transaction types
    
    Future: Could use FinBERT or similar financial domain model.
    """
    
    def __init__(self, language: str = "en"):
        self.language = language
        self.supported_entities = [
            "TRANSACTION_AMOUNT",
            "CURRENCY",
            "COMPANY_NAME",
            "TRANSACTION_TYPE",
        ]
    
    def load(self):
        """Load financial NER model."""
        print(f"⚠ FinancialEntityRecognizer for {self.language} not yet implemented")
        print(f"  Supported entities: {', '.join(self.supported_entities)}")
        print(f"  Future: Will use FinBERT or similar for financial NER")
    
    def analyze(self, text: str) -> list:
        """Analyze text for financial entities."""
        return []


def create_custom_recognizer(
    entity_type: str,
    patterns: list[str],
    context_words: list[str] | None = None,
    score: float = 0.85,
) -> Any:
    """Create a custom Presidio PatternRecognizer.
    
    This is the user-facing API for adding company-specific entity patterns.
    
    Args:
        entity_type: Entity type name (e.g., "EMPLOYEE_ID", "PROJECT_CODE")
        patterns: List of regex patterns
        context_words: Optional context words that boost confidence
        score: Base confidence score
    
    Returns:
        Presidio PatternRecognizer
    
    Example:
        # Detect internal employee IDs
        recognizer = create_custom_recognizer(
            entity_type="EMPLOYEE_ID",
            patterns=[r"\\bEMP\\d{6}\\b"],
            context_words=["employee", "staff", "worker"],
            score=0.9,
        )
        
        # Add to analyzer
        analyzer.add_recognizer(recognizer)
    """
    try:
        from presidio_analyzer import Pattern, PatternRecognizer  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "Presidio not installed. Install with: pip install 'pii-firewall[presidio]'"
        ) from exc
    
    # Create Presidio Pattern objects
    presidio_patterns = [
        Pattern(name=f"{entity_type}_{i}", regex=pattern, score=score)
        for i, pattern in enumerate(patterns)
    ]
    
    # Create recognizer
    recognizer = PatternRecognizer(
        supported_entity=entity_type,
        patterns=presidio_patterns,
        context=context_words,
    )
    
    return recognizer


# =============================================================================
# DOMAIN RECOGNIZER REGISTRY
# =============================================================================

DOMAIN_RECOGNIZERS = {
    "medical_entities": MedicalEntityRecognizer,
    "financial_entities": FinancialEntityRecognizer,
    # Future: Add more domain recognizers here
}


def get_domain_recognizer(domain: str, language: str = "en") -> Any:
    """Get a domain-specific recognizer by name.
    
    Args:
        domain: Domain name (e.g., "medical_entities")
        language: Language code
    
    Returns:
        Domain recognizer instance
    """
    if domain not in DOMAIN_RECOGNIZERS:
        raise ValueError(f"Unknown domain recognizer: {domain}")
    
    recognizer_class = DOMAIN_RECOGNIZERS[domain]
    return recognizer_class(language=language)
