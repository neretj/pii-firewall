from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from src.privacy_firewall.firewall import create_firewall

TEST_CONTEXT = {
    "tenant_id": "test-tenant",
    "case_id": "test-case",
    "thread_id": "test-thread",
    "actor_id": "test-user",
}


class DummyResponse:
    def __init__(self, body: str) -> None:
        self._body = body.encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_transformer_remote_inference_uses_remote_engine() -> None:
    firewall = create_firewall(
        domain="generic",
        language="en",
        detector_backend="transformers",
        transformer_use_remote=True,
        transformer_remote_url="https://api.example.com/ner",
        transformer_remote_api_key="test-secret",
        transformer_model_id="dslim/bert-base-NER",
    )

    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(request.header_items())
        payload = [
            {
                "entity_group": "PER",
                "word": "Ana Garcia",
                "start": 10,
                "end": 20,
                "score": 0.99,
            }
        ]
        return DummyResponse(json.dumps(payload))

    with patch(
        "src.privacy_firewall.transformers_ner.engine.urllib.request.urlopen",
        side_effect=fake_urlopen,
    ):
        result = firewall.anonymize(text="My friend Ana Garcia arrived.", context=TEST_CONTEXT)

    assert captured["url"] == "https://api.example.com/ner"
    assert captured["timeout"] == 30.0
    assert captured["headers"].get("Authorization") == "Bearer test-secret"
    assert any(
        entity["entity_type"] == "PERSON" and entity["text"] == "Ana Garcia"
        for entity in result.trace.detected_entities
    )


def test_transformer_remote_requires_remote_url() -> None:
    firewall = create_firewall(
        domain="generic",
        language="en",
        detector_backend="transformers",
        transformer_use_remote=True,
        transformer_model_id="dslim/bert-base-NER",
    )

    with pytest.raises(ValueError, match="transformer_use_remote=True requires transformer_remote_url"):
        firewall.anonymize(text="Hi Ana.", context=TEST_CONTEXT)
