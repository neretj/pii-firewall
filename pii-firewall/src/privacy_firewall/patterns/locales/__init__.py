"""Locale-specific pattern modules.

This package contains one file per locale for easy extension.
To add a new locale, create a new file (e.g., nl_patterns.py) and import it here.
"""

from .global_patterns import GLOBAL_PATTERNS
from .es_patterns import ES_PATTERNS
from .us_patterns import US_PATTERNS
from .fr_patterns import FR_PATTERNS
from .de_patterns import DE_PATTERNS
from .it_patterns import IT_PATTERNS
from .pt_patterns import PT_PATTERNS

LOCALE_PATTERNS = (
    GLOBAL_PATTERNS +
    ES_PATTERNS +
    US_PATTERNS +
    FR_PATTERNS +
    DE_PATTERNS +
    IT_PATTERNS +
    PT_PATTERNS
)

__all__ = [
    "LOCALE_PATTERNS",
    "GLOBAL_PATTERNS",
    "ES_PATTERNS",
    "US_PATTERNS",
    "FR_PATTERNS",
    "DE_PATTERNS",
    "IT_PATTERNS",
    "PT_PATTERNS",
]
