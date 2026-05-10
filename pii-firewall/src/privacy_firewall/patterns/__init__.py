"""Pattern catalog system for locale-aware regex patterns."""

from .catalog import PatternCatalog, EntityPattern, create_default_catalog
from .locales import LOCALE_PATTERNS

__all__ = ["PatternCatalog", "EntityPattern", "LOCALE_PATTERNS", "create_default_catalog"]
