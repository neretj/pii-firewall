from __future__ import annotations

import re

# Defensive residual patterns used post-sanitization.
DNI_REGEX = re.compile(r"\b\d{8}[A-Z]\b")
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_REGEX = re.compile(r"\b(?:\+34\s?)?(?:6|7|9)\d{8}\b")


def has_residual_pii(text: str) -> bool:
    return bool(DNI_REGEX.search(text) or EMAIL_REGEX.search(text) or PHONE_REGEX.search(text))


def apply_residual_cleanup(text: str) -> tuple[str, list[dict]]:
    """Apply defensive anonymization to residual regex-detectable PII."""
    cleaned = text
    replacements: list[dict] = []

    # Process in reverse order by position to maintain offsets
    matches: list[tuple[int, int, str, str]] = []

    for m in DNI_REGEX.finditer(text):
        matches.append((m.start(), m.end(), m.group(0), "NATIONAL_ID"))
    for m in EMAIL_REGEX.finditer(text):
        matches.append((m.start(), m.end(), m.group(0), "EMAIL"))
    for m in PHONE_REGEX.finditer(text):
        matches.append((m.start(), m.end(), m.group(0), "PHONE_NUMBER"))

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
