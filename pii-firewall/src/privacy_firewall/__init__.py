"""Privacy Firewall public API."""

from __future__ import annotations

from typing import Any

from .types import ProcessResult, Entity, TraceRecord
from .vault import InMemoryMappingVault, SQLiteMappingVault
from .llm import MockLLMClient, LLMClientProtocol, call_model
from .firewall import PrivacyFirewall, create_firewall
from .profiles import (
    DomainProfile,
    EntityDisposition,
    DispositionAction,
    GENERIC_PROFILE,
    HEALTHCARE_PROFILE,
    FINANCE_PROFILE,
    LEGAL_PROFILE,
    PRESET_PROFILES,
    list_preset_profiles,
    get_preset_profile,
    create_custom_profile,
)
from .patterns import PatternCatalog, EntityPattern, create_default_catalog
from .language import LanguageDetector, LanguageRouter
from .unified_detector import UnifiedDetectionEngine
from .anonymization_engine import AnonymizationEngine
from .sdk import PrivacyFirewallSDK


def create_app(*args: Any, **kwargs: Any) -> Any:
    """Create the optional FastAPI app.

    This indirection keeps base installs importable without the `web` extra.
    """
    from .web import create_app as _create_app

    return _create_app(*args, **kwargs)

__all__ = [
    # Core runtime
    "PrivacyFirewall",
    "create_firewall",

    # Shared runtime dependencies
    "InMemoryMappingVault",
    "SQLiteMappingVault",
    "MockLLMClient",
    "LLMClientProtocol",
    "call_model",
    "create_app",
    "ProcessResult",
    "Entity",
    "TraceRecord",

    # Profiles and policy-by-disposition
    "DomainProfile",
    "EntityDisposition",
    "DispositionAction",
    "GENERIC_PROFILE",
    "HEALTHCARE_PROFILE",
    "FINANCE_PROFILE",
    "LEGAL_PROFILE",
    "PRESET_PROFILES",
    "list_preset_profiles",
    "get_preset_profile",
    "create_custom_profile",

    # Detection/anonymization components
    "PatternCatalog",
    "EntityPattern",
    "create_default_catalog",
    "LanguageDetector",
    "LanguageRouter",
    "UnifiedDetectionEngine",
    "AnonymizationEngine",
    "PrivacyFirewallSDK",
]
