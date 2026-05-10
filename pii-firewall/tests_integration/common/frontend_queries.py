from __future__ import annotations

import re
from pathlib import Path

FRONTEND_LANGUAGES = ["es", "en", "fr", "de", "it", "pt"]
FRONTEND_PROFILES = ["generic", "healthcare", "finance", "legal"]


def frontend_constants_path() -> Path:
    return Path(__file__).resolve().parents[3] / "pii-web-next" / "lib" / "constants.ts"


def load_frontend_queries() -> dict[str, list[str]]:
    raw = frontend_constants_path().read_text(encoding="utf-8")

    match = re.search(
        r"export const DEMO_PROMPTS_BY_LANGUAGE: Record<string, string\[]> = \{(.*?)\n\};",
        raw,
        re.S,
    )
    if not match:
        raise AssertionError("Could not parse DEMO_PROMPTS_BY_LANGUAGE from frontend constants.ts")

    block = match.group(1)
    queries_by_language: dict[str, list[str]] = {}

    for language_match in re.finditer(r"\s*([a-z]{2}): \[(.*?)\],", block, re.S):
        language = language_match.group(1)
        language_block = language_match.group(2)
        prompts = re.findall(r'"((?:[^"\\]|\\.)*)"', language_block)
        queries_by_language[language] = [
            p.replace('\\"', '"').replace("\\n", "\n") for p in prompts
        ]

    return queries_by_language
