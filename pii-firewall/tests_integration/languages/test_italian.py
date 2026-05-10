from __future__ import annotations

from tests_integration.common.e2e_matrix import (
    run_language_mapping_and_hydration,
    run_language_queries_matrix,
)


def test_italian_all_frontend_queries_all_profiles_all_engines(api_client, runtime_options) -> None:
    assert "it" in runtime_options["language"]
    run_language_queries_matrix(api_client, "it")


def test_italian_mapping_and_rehydration_all_profiles_all_engines(api_client, runtime_options) -> None:
    assert "it" in runtime_options["language"]
    run_language_mapping_and_hydration(api_client, "it")
