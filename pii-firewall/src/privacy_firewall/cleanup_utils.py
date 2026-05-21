from __future__ import annotations

import re

# Last-resort patterns run after the main pipeline to catch anything that slipped through.
DNI_REGEX = re.compile(r"\b\d{8}[A-Z]\b")
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_REGEX = re.compile(r"\b(?:\+34\s?)?(?:6|7|9)\d{8}\b")
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
IBAN_REGEX = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")
CREDIT_CARD_REGEX = re.compile(
    r"\b(?:4\d{12}(?:\d{3})?|5[1-5]\d{14}|3[47]\d{13}|6(?:011|5\d{2})\d{12})\b"
)

_ALL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (DNI_REGEX, "NATIONAL_ID"),
    (EMAIL_REGEX, "EMAIL"),
    (PHONE_REGEX, "PHONE_NUMBER"),
    (SSN_REGEX, "SSN"),
    (IBAN_REGEX, "IBAN"),
    (CREDIT_CARD_REGEX, "CREDIT_CARD"),
]


def has_residual_pii(text: str) -> bool:
    return any(pattern.search(text) for pattern, _ in _ALL_PATTERNS)


def apply_residual_cleanup(text: str) -> tuple[str, list[dict]]:
    """Apply defensive anonymization to residual regex-detectable PII."""
    cleaned = text
    replacements: list[dict] = []

    # Process in reverse order by position to maintain offsets
    matches: list[tuple[int, int, str, str]] = []

    for pattern, entity_type in _ALL_PATTERNS:
        for m in pattern.finditer(text):
            matches.append((m.start(), m.end(), m.group(0), entity_type))

    for start, end, original, entity_type in sorted(matches, key=lambda x: x[0], reverse=True):
        replacement = f"[{entity_type}]"
        cleaned = cleaned[:start] + replacement + cleaned[end:]
        replacements.append(
            {
                "entity_type": entity_type,
                "source": "residual_cleanup",
                "from": original,
                "to": replacement,
            }
        )

    return cleaned, list(reversed(replacements))
