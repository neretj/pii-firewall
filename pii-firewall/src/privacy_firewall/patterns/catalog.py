"""Pattern catalog for locale-aware entity detection.

This module provides a centralized catalog of regex patterns organized by:
- Entity type (EMAIL, PHONE, SSN, etc.)
- Locale (ES, US, FR, DE, GLOBAL)

Benefits:
- No hardcoded patterns in logic code
- Easy to add new locales/patterns without code changes
- Can be loaded from external config (YAML/JSON) in future
- Patterns can be contributed by users for company-specific entities
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class EntityPattern:
    """A regex pattern for detecting an entity type in a specific locale.
    
    Attributes:
        entity_type: Type of entity (e.g., 'PHONE', 'EMAIL', 'SSN')
        locale: Locale code (e.g., 'ES', 'US', 'FR', 'GLOBAL')
        pattern: Compiled regex pattern
        confidence: Base confidence score (0.0-1.0)
        context_words: Optional list of words that boost confidence when nearby
        description: Human-readable description
    """
    
    entity_type: str
    locale: str
    pattern: re.Pattern
    confidence: float = 1.0
    context_words: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""
    
    def match(self, text: str) -> list[tuple[str, int, int]]:
        """Find all matches in text. Returns list of (matched_text, start, end)."""
        return [(m.group(0), m.start(), m.end()) for m in self.pattern.finditer(text)]


class PatternCatalogProtocol(Protocol):
    """Protocol for pattern catalog implementations."""
    
    def get_patterns(self, entity_type: str, locale: str) -> list[EntityPattern]:
        """Get all patterns for entity type in locale."""
        ...
    
    def add_pattern(self, pattern: EntityPattern) -> None:
        """Add a new pattern to catalog."""
        ...


@dataclass
class PatternCatalog:
    """Centralized catalog of entity detection patterns.
    
    Patterns are organized by (entity_type, locale) and support:
    - Locale-specific patterns (e.g., ES_DNI only for Spain)
    - Global patterns (apply to all locales)
    - Fallback chain (try locale-specific first, then GLOBAL)
    - Runtime pattern registration (for custom company patterns)
    """
    
    # Internal storage: {(entity_type, locale): [patterns]}
    _patterns: dict[tuple[str, str], list[EntityPattern]] = field(default_factory=dict, init=False, repr=False)
    
    def add_pattern(self, pattern: EntityPattern) -> None:
        """Register a pattern in the catalog."""
        key = (pattern.entity_type, pattern.locale)
        if key not in self._patterns:
            self._patterns[key] = []
        self._patterns[key].append(pattern)
    
    def get_patterns(self, entity_type: str, locale: str) -> list[EntityPattern]:
        """Get patterns for entity type, with locale fallback.
        
        Returns:
            - Locale-specific patterns if available
            - GLOBAL patterns otherwise
            - Empty list if no patterns found
        """
        # Try locale-specific first
        key = (entity_type, locale)
        if key in self._patterns:
            return self._patterns[key]
        
        # Fallback to GLOBAL
        global_key = (entity_type, "GLOBAL")
        if global_key in self._patterns:
            return self._patterns[global_key]
        
        return []
    
    def get_all_patterns_for_locale(self, locale: str) -> list[EntityPattern]:
        """Get all patterns applicable to a locale (locale-specific + GLOBAL)."""
        patterns = []
        
        for (entity_type, pattern_locale), pattern_list in self._patterns.items():
            if pattern_locale == locale or pattern_locale == "GLOBAL":
                patterns.extend(pattern_list)
        
        return patterns
    
    def list_entity_types(self, locale: str | None = None) -> set[str]:
        """List all entity types in catalog, optionally filtered by locale."""
        if locale is None:
            return {entity_type for entity_type, _ in self._patterns.keys()}
        
        return {
            entity_type
            for entity_type, pattern_locale in self._patterns.keys()
            if pattern_locale == locale or pattern_locale == "GLOBAL"
        }
    
    def remove_pattern(self, entity_type: str, locale: str) -> int:
        """Remove all patterns for entity type in locale. Returns count removed."""
        key = (entity_type, locale)
        if key in self._patterns:
            count = len(self._patterns[key])
            del self._patterns[key]
            return count
        return 0
    
    @classmethod
    def from_dict(cls, config: dict) -> "PatternCatalog":
        """Create catalog from configuration dictionary.
        
        Format:
        {
            "patterns": [
                {
                    "entity_type": "PHONE_NUMBER"  # e.g. ET.PHONE_NUMBER,
                    "locale": "ES",
                    "pattern": r"\\b(?:\\+34\\s?)?(?:6|7|9)\\d{8}\\b",
                    "confidence": 1.0,
                    "description": "Spanish phone numbers"
                }
            ]
        }
        """
        catalog = cls()
        
        for pattern_config in config.get("patterns", []):
            pattern = EntityPattern(
                entity_type=pattern_config["entity_type"],
                locale=pattern_config["locale"],
                pattern=re.compile(pattern_config["pattern"]),
                confidence=pattern_config.get("confidence", 1.0),
                context_words=tuple(pattern_config.get("context_words", [])),
                description=pattern_config.get("description", ""),
            )
            catalog.add_pattern(pattern)
        
        return catalog
    
    def to_dict(self) -> dict:
        """Export catalog to configuration dictionary."""
        patterns_list = []
        
        for pattern_list in self._patterns.values():
            for pattern in pattern_list:
                patterns_list.append({
                    "entity_type": pattern.entity_type,
                    "locale": pattern.locale,
                    "pattern": pattern.pattern.pattern,
                    "confidence": pattern.confidence,
                    "context_words": list(pattern.context_words),
                    "description": pattern.description,
                })
        
        return {"patterns": patterns_list}


def create_default_catalog() -> PatternCatalog:
    """Create catalog with all default patterns from locales module."""
    from .locales import LOCALE_PATTERNS
    
    catalog = PatternCatalog()
    
    for pattern in LOCALE_PATTERNS:
        catalog.add_pattern(pattern)
    
    return catalog
