from __future__ import annotations

import json
import re
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

# Ensure local package imports work when running as a script.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.privacy_firewall.web.app import create_app
from tests_integration.common.frontend_queries import load_frontend_queries

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d .-]{7,}\d")
DENSE_ID_RE = re.compile(r"\b[A-Z]{0,4}\d{6,}[A-Z0-9]*\b")

LANG_ORDER = ["es", "en", "fr", "de", "it", "pt"]

UNAVAILABLE_MARKERS = [
    "No module named",
    "not installed",
    "requires",
    "ImportError",
    "ModuleNotFoundError",
    "cannot import name",
]


def expected_structured_pii(text: str) -> list[str]:
    values: set[str] = set(EMAIL_RE.findall(text))
    values.update(match.group(0) for match in PHONE_RE.finditer(text))
    values.update(match.group(0) for match in DENSE_ID_RE.finditer(text))
    cleaned = sorted({v.strip() for v in values if v.strip()}, key=len, reverse=True)
    result: list[str] = []
    for value in cleaned:
        if any(value in kept for kept in result):
            continue
        result.append(value)
    return sorted(result)


def _is_engine_unavailable(response_text: str) -> bool:
    return any(marker in response_text for marker in UNAVAILABLE_MARKERS)


def run_audit(*, backend: str, profile: str) -> dict:
    client = TestClient(create_app())
    prompts = load_frontend_queries()

    out: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "backend": backend,
        "profile": profile,
        "languages": {},
    }

    for language in LANG_ORDER:
        queries = prompts.get(language, [])
        language_result = {
            "total_queries": len(queries),
            "http_failures": [],
            "structured_expected": 0,
            "structured_fully_sanitized": 0,
            "query_results": [],
        }

        for idx, query in enumerate(queries, start=1):
            payload = {
                "text": query,
                "tenant_id": f"audit-tenant-{language}",
                "case_id": "audit-case",
                "thread_id": f"audit-thread-{language}",
                "actor_id": "audit-user",
                "profile": profile,
                "language": language,
                "detector_backend": backend,
            }

            response = client.post("/api/run", json=payload)
            if response.status_code != 200:
                unavailable = response.status_code == 500 and _is_engine_unavailable(response.text)
                language_result["http_failures"].append(
                    {
                        "idx": idx,
                        "status": response.status_code,
                        "unavailable": unavailable,
                        "detail": response.text,
                    }
                )
                continue

            data = response.json()
            sanitized = data["steps"]["sanitized_text"]
            expected = expected_structured_pii(query)
            missing = [v for v in expected if v in sanitized]

            if expected:
                language_result["structured_expected"] += 1
                if not missing:
                    language_result["structured_fully_sanitized"] += 1

            language_result["query_results"].append(
                {
                    "idx": idx,
                    "blocked": data["steps"]["blocked"],
                    "detected_entities": len(data["steps"]["detected_entities"]),
                    "mapping_size": len(data["steps"]["mapping"]),
                    "expected_structured": expected,
                    "still_present_after_sanitize": missing,
                }
            )

        out["languages"][language] = language_result

    return out


def write_markdown(report: dict, path: Path) -> None:
    lines: list[str] = []
    lines.append(f"# {report['backend']} Audit Results")
    lines.append("")
    lines.append(f"- Generated: {report['generated_at']}")
    lines.append(f"- Backend: {report['backend']}")
    lines.append(f"- Profile: {report['profile']}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Language | Queries | HTTP Failures | Unavailable Failures | Structured Expected | Structured Fully Sanitized |")
    lines.append("|---|---:|---:|---:|---:|---:|")

    for language in LANG_ORDER:
        r = report["languages"][language]
        unavailable_failures = sum(1 for failure in r["http_failures"] if failure.get("unavailable"))
        lines.append(
            f"| {language} | {r['total_queries']} | {len(r['http_failures'])} | {unavailable_failures} | {r['structured_expected']} | {r['structured_fully_sanitized']} |"
        )

    lines.append("")
    lines.append("## Detailed Findings")
    lines.append("")

    for language in LANG_ORDER:
        r = report["languages"][language]
        lines.append(f"### {language}")
        lines.append("")

        if r["http_failures"]:
            lines.append("HTTP failures:")
            for fail in r["http_failures"]:
                suffix = " (engine unavailable)" if fail.get("unavailable") else ""
                lines.append(
                    f"- idx {fail['idx']}: HTTP {fail['status']}{suffix} - {fail['detail'][:180]}"
                )
        else:
            lines.append("HTTP failures: none")

        problematic = [
            q for q in r["query_results"] if q["still_present_after_sanitize"]
        ]
        if problematic:
            lines.append("Structured PII still present after sanitize:")
            for q in problematic:
                lines.append(
                    f"- idx {q['idx']}: {q['still_present_after_sanitize']}"
                )
        else:
            lines.append("Structured PII sanitization gaps: none detected")

        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit a detector backend across frontend queries.")
    parser.add_argument(
        "--backend",
        default="presidio",
        help="detector backend to test (default: presidio)",
    )
    parser.add_argument(
        "--profile",
        default="generic",
        help="profile to use for audit (default: generic)",
    )
    args = parser.parse_args()

    result = run_audit(backend=args.backend, profile=args.profile)

    reports_dir = Path(__file__).resolve().parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    backend_slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", args.backend.strip())
    json_path = reports_dir / f"{backend_slug}_audit_results.json"
    md_path = reports_dir / f"{backend_slug}_audit_results.md"

    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(result, md_path)

    print(f"[AUDIT] JSON report: {json_path}")
    print(f"[AUDIT] Markdown report: {md_path}")
