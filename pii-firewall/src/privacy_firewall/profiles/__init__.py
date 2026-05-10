"""Domain profiles and entity disposition system."""

from .profiles import DomainProfile, EntityDisposition, DispositionAction
from .presets import (
    GENERIC_PROFILE,
    HEALTHCARE_PROFILE,
    FINANCE_PROFILE,
    LEGAL_PROFILE,
    PRESET_PROFILES,
    list_preset_profiles,
    get_preset_profile,
    create_custom_profile,
)

__all__ = [
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
]
