"""
Pytest fixtures compartidas para todos los tests de integración.
"""

import logging
import warnings

import pytest
from fastapi.testclient import TestClient

from src.privacy_firewall.firewall import create_firewall
from src.privacy_firewall.vault import InMemoryMappingVault
from src.privacy_firewall.llm import MockLLMClient
from src.privacy_firewall.web.app import create_app


@pytest.fixture(scope="session", autouse=True)
def _configure_test_logging_and_warnings():
    """Reduce known-noisy warnings so test failures remain visible."""
    logging.getLogger("presidio-analyzer").setLevel(logging.ERROR)

    # Known third-party warning noise in this environment (non-blocking).
    warnings.filterwarnings("ignore", category=DeprecationWarning, message=r".*SwigPyPacked.*")
    warnings.filterwarnings("ignore", category=DeprecationWarning, message=r".*SwigPyObject.*")
    warnings.filterwarnings("ignore", category=DeprecationWarning, message=r".*swigvarlink.*")
    warnings.filterwarnings("ignore", category=DeprecationWarning, message=r".*torch\.jit\.script.*")
    warnings.filterwarnings("ignore", category=DeprecationWarning, message=r".*check_label_groups is deprecated.*")
    warnings.filterwarnings("ignore", category=UserWarning, message=r".*resume_download.*deprecated.*")


@pytest.fixture
def vault():
    """Vault compartido para tests."""
    return InMemoryMappingVault()


@pytest.fixture
def llm_client():
    """LLM mock para tests."""
    return MockLLMClient(prefix="[MOCK_LLM]")


@pytest.fixture
def firewall_healthcare_es(vault, llm_client):
    """Firewall configurado para healthcare en español."""
    return create_firewall(
        domain="healthcare",
        language="es",
        detector_backend="presidio",
        vault=vault,
        llm_client=llm_client,
    )


@pytest.fixture
def firewall_healthcare_en(vault, llm_client):
    """Firewall configurado para healthcare en inglés."""
    return create_firewall(
        domain="healthcare",
        language="en",
        detector_backend="presidio",
        vault=vault,
        llm_client=llm_client,
    )


@pytest.fixture
def firewall_healthcare_fr(vault, llm_client):
    """Firewall configurado para healthcare en francés."""
    return create_firewall(
        domain="healthcare",
        language="fr",
        detector_backend="presidio",
        vault=vault,
        llm_client=llm_client,
    )


@pytest.fixture
def test_context():
    """Context estándar para tests."""
    return {
        "tenant_id": "test-tenant",
        "case_id": "test-case",
        "thread_id": "test-thread",
        "actor_id": "test-user",
    }


def assert_entity_detected(result, entity_type, expected_text=None):
    """Helper: Verificar que una entidad fue detectada.
    
    Args:
        result: ProcessResult del firewall
        entity_type: Tipo de entidad esperada (ej: "PERSON", "PHONE_NUMBER")
        expected_text: Texto esperado (opcional, busca substring)
    
    Returns:
        True si la entidad fue detectada, False otherwise
    """
    detected = result.trace.detected_entities
    
    for entity in detected:
        if entity["entity_type"] == entity_type:
            if expected_text is None:
                return True
            if expected_text in entity["text"]:
                return True
    
    return False


def get_entity(result, entity_type):
    """Helper: Obtener primera entidad del tipo especificado.
    
    Args:
        result: ProcessResult del firewall
        entity_type: Tipo de entidad
    
    Returns:
        Dict de la entidad o None si no se encuentra
    """
    for entity in result.trace.detected_entities:
        if entity["entity_type"] == entity_type:
            return entity
    return None


def assert_sanitized(result, original_pii, should_be_removed=True):
    """Helper: Verificar que PII fue sanitizada o preservada.
    
    Args:
        result: ProcessResult del firewall
        original_pii: Texto PII original (ej: "12345678A", "+34612345678")
        should_be_removed: True si debe estar sanitizado, False si debe preservarse
    """
    sanitized = result.sanitized_text
    is_present = original_pii in sanitized
    
    if should_be_removed:
        assert not is_present, f"PII '{original_pii}' NO fue sanitizada: {sanitized}"
    else:
        assert is_present, f"PII '{original_pii}' fue sanitizada incorrectamente: {sanitized}"


@pytest.fixture(scope="session")
def api_client():
    """FastAPI TestClient compartido para pruebas E2E por API."""
    return TestClient(create_app())


@pytest.fixture(scope="session")
def runtime_options(api_client):
    """Opciones de runtime expuestas por /api/runtime-options."""
    response = api_client.get("/api/runtime-options")
    assert response.status_code == 200, response.text
    return response.json()
