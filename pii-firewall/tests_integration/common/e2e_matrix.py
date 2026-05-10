from __future__ import annotations

import re
from typing import Any

from tests_integration.common.frontend_queries import FRONTEND_PROFILES, load_frontend_queries

DETECTION_ENGINES = [
    "regex",
    "presidio",
    "opf",
    "gliner",
    "nemotron",
    "transformers",
    "hybrid",
]

UNAVAILABLE_MARKERS = [
    "No module named",
    "not installed",
    "requires",
    "ImportError",
    "ModuleNotFoundError",
    "cannot import name",
]


def _log(message: str) -> None:
    print(f"[E2E] {message}", flush=True)


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d .-]{7,}\d")
DENSE_ID_RE = re.compile(r"\b[A-Z]{0,4}\d{6,}[A-Z0-9]*\b")


def _expected_structured_pii(text: str) -> set[str]:
    values = set(EMAIL_RE.findall(text))
    values.update(match.group(0) for match in PHONE_RE.finditer(text))
    values.update(match.group(0) for match in DENSE_ID_RE.finditer(text))
    cleaned = sorted({v.strip() for v in values if v.strip()}, key=len, reverse=True)
    result: list[str] = []
    for value in cleaned:
        if any(value in kept for kept in result):
            continue
        result.append(value)
    return set(result)


def assert_api_response_contract(data: dict[str, Any]) -> None:
    assert "input" in data
    assert "steps" in data
    assert "trace" in data

    for key in ["text", "context", "config"]:
        assert key in data["input"]

    for key in [
        "detected_entities",
        "sanitized_text",
        "blocked",
        "block_reason",
        "llm_request",
        "llm_response",
        "rehydrated_output",
        "mapping",
        "cleanup_warnings",
    ]:
        assert key in data["steps"]

    for key in ["trace_id", "profile", "total_replacements"]:
        assert key in data["trace"]


def _base_payload(language: str, profile: str, engine: str, *, case_id: str, thread_id: str) -> dict[str, Any]:
    return {
        "tenant_id": f"tenant-{language}-{profile}-{engine}",
        "case_id": case_id,
        "thread_id": thread_id,
        "actor_id": "user-e2e",
        "profile": profile,
        "language": language,
        "detector_backend": engine,
    }


def _engine_error_is_unavailable(response_text: str) -> bool:
    return any(marker in response_text for marker in UNAVAILABLE_MARKERS)


def run_language_queries_matrix(client: Any, language: str) -> None:
    queries = load_frontend_queries()[language]
    failures: list[str] = []
    unavailable_engines: set[str] = set()
    executed_runs = 0

    _log(f"START queries matrix: language={language}, queries={len(queries)}")

    for profile in FRONTEND_PROFILES:
        for engine in DETECTION_ENGINES:
            if engine in unavailable_engines:
                _log(f"SKIP engine={engine} profile={profile} (previously marked unavailable)")
                continue

            _log(f"RUN engine={engine} profile={profile} language={language}")
            engine_unavailable = False
            for idx, query in enumerate(queries, start=1):
                _log(
                    f"POST /api/run engine={engine} profile={profile} language={language} "
                    f"query={idx}/{len(queries)} text={query}"
                )
                payload = {
                    **_base_payload(
                        language,
                        profile,
                        engine,
                        case_id=f"case-queries-{language}",
                        thread_id=f"thread-q{idx}",
                    ),
                    "text": query,
                }

                response = client.post("/api/run", json=payload)

                if response.status_code == 500 and _engine_error_is_unavailable(response.text):
                    unavailable_engines.add(engine)
                    engine_unavailable = True
                    _log(
                        f"UNAVAILABLE engine={engine} language={language} profile={profile} reason={response.text[:180]}"
                    )
                    break

                if response.status_code != 200:
                    _log(
                        f"ERROR engine={engine} profile={profile} language={language} query={idx} status={response.status_code}"
                    )
                    failures.append(
                        f"HTTP {response.status_code} for lang={language}, profile={profile}, engine={engine}, idx={idx}: {response.text}"
                    )
                    continue

                data = response.json()
                executed_runs += 1
                _log(
                    f"OK engine={engine} profile={profile} language={language} query={idx} blocked={data['steps']['blocked']} replacements={data['trace']['total_replacements']}"
                )

                try:
                    assert_api_response_contract(data)
                    assert data["input"]["config"]["profile"] == profile
                    assert data["input"]["config"]["detector_backend"] == engine

                    if engine == "regex":
                        expected_pii = _expected_structured_pii(query)
                        sanitized = data["steps"]["sanitized_text"]
                        for pii in expected_pii:
                            assert pii not in sanitized, (
                                f"regex engine did not sanitize structured PII '{pii}' "
                                f"for lang={language}, profile={profile}, idx={idx}"
                            )
                except AssertionError as exc:
                    failures.append(
                        f"Contract assertion failed for lang={language}, profile={profile}, engine={engine}, idx={idx}: {exc}"
                    )

            if engine_unavailable:
                continue

    _log(f"END queries matrix: language={language}, executed_runs={executed_runs}, failures={len(failures)}")
    assert executed_runs > 0, f"No engine was operational for language={language}"
    assert not failures, "\n".join(failures[:30])


def run_language_mapping_and_hydration(client: Any, language: str) -> None:
    queries = load_frontend_queries()[language]
    failures: list[str] = []
    unavailable_engines: set[str] = set()
    executed_runs = 0

    _log(f"START mapping/rehydration matrix: language={language}, queries={len(queries)}")

    for profile in FRONTEND_PROFILES:
        for engine in DETECTION_ENGINES:
            if engine in unavailable_engines:
                _log(f"SKIP engine={engine} profile={profile} (previously marked unavailable)")
                continue

            case_id = f"case-map-{language}-{profile}-{engine}"
            thread_id = "thread-mapping"
            mapping_sizes: list[int] = []
            engine_unavailable = False
            _log(f"RUN mapping engine={engine} profile={profile} language={language}")

            for idx, query in enumerate(queries, start=1):
                _log(
                    f"POST /api/run(mapping) engine={engine} profile={profile} language={language} "
                    f"query={idx}/{len(queries)} text={query}"
                )
                payload = {
                    **_base_payload(language, profile, engine, case_id=case_id, thread_id=thread_id),
                    "text": query,
                }

                response = client.post("/api/run", json=payload)

                if response.status_code == 500 and _engine_error_is_unavailable(response.text):
                    unavailable_engines.add(engine)
                    engine_unavailable = True
                    _log(
                        f"UNAVAILABLE engine={engine} language={language} profile={profile} reason={response.text[:180]}"
                    )
                    break

                if response.status_code != 200:
                    _log(
                        f"ERROR engine={engine} profile={profile} language={language} query={idx} status={response.status_code}"
                    )
                    failures.append(
                        f"HTTP {response.status_code} for lang={language}, profile={profile}, engine={engine}, idx={idx}: {response.text}"
                    )
                    break

                data = response.json()
                executed_runs += 1
                _log(
                    f"OK mapping engine={engine} profile={profile} language={language} query={idx} blocked={data['steps']['blocked']} map_size={len(data['steps']['mapping'])}"
                )

                try:
                    assert_api_response_contract(data)
                    mapping = data["steps"]["mapping"]
                    assert isinstance(mapping, dict)
                    mapping_sizes.append(len(mapping))

                    if engine == "regex":
                        expected_pii = _expected_structured_pii(query)
                        sanitized = data["steps"]["sanitized_text"]
                        for pii in expected_pii:
                            assert pii not in sanitized, (
                                f"regex engine did not sanitize structured PII '{pii}' "
                                f"for lang={language}, profile={profile}, idx={idx}"
                            )

                    if not data["steps"]["blocked"]:
                        llm_response = data["steps"]["llm_response"]
                        rehydrated = data["steps"]["rehydrated_output"]

                        assert llm_response is not None
                        assert rehydrated is not None

                        # Rehydration invariant: if token appears in llm_response,
                        # its original value should appear in rehydrated text.
                        for token, original in mapping.items():
                            if token in llm_response:
                                assert str(original) in rehydrated
                except AssertionError as exc:
                    failures.append(
                        f"Mapping/rehydration assertion failed for lang={language}, profile={profile}, engine={engine}, idx={idx}: {exc}"
                    )

            if engine_unavailable:
                continue

            if mapping_sizes and mapping_sizes[-1] > 0:
                _log(f"POST /api/forget engine={engine} profile={profile} language={language}")
                forget_payload = {
                    **_base_payload(language, profile, engine, case_id=case_id, thread_id=thread_id),
                    "text": "_",
                }
                forget_response = client.post("/api/forget", json=forget_payload)
                if forget_response.status_code != 200:
                    _log(
                        f"ERROR forget engine={engine} profile={profile} language={language} status={forget_response.status_code}"
                    )
                    failures.append(
                        f"Forget failed for lang={language}, profile={profile}, engine={engine}: {forget_response.text}"
                    )
                else:
                    _log(
                        f"OK forget engine={engine} profile={profile} language={language} removed={forget_response.json().get('removed')}"
                    )
                    removed = forget_response.json().get("removed")
                    if not isinstance(removed, int):
                        failures.append(
                            f"Forget response malformed for lang={language}, profile={profile}, engine={engine}: {forget_response.text}"
                        )

    _log(f"END mapping/rehydration matrix: language={language}, executed_runs={executed_runs}, failures={len(failures)}")
    assert executed_runs > 0, f"No engine was operational for language={language}"
    assert not failures, "\n".join(failures[:30])
