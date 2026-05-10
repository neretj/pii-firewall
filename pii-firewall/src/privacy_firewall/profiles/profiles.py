"""Domain profile system with entity dispositions.

This module replaces the simple Policy class with a rich profile system that
declares what to do with each entity type based on domain context.

Key concepts:
- DispositionAction: What to do with an entity (keep, redact, pseudonymize, etc.)
- EntityDisposition: Maps entity type to action + parameters
- DomainProfile: Collection of dispositions for a use case (healthcare, finance, etc.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DispositionAction(Enum):
    """Actions that can be taken on detected entities."""
    
    KEEP = "keep"  # Keep entity as-is (domain-relevant data)
    REDACT = "redact"  # Replace with [REDACTED] or generic token
    PSEUDONYMIZE = "pseudonymize"  # Replace with reversible token (PERSON_1)
    GENERALIZE = "generalize"  # Replace with coarser value (age 43 → 40-49)
    MASK = "mask"  # Partial obscurement (credit card 4111...1111)
    HASH = "hash"  # Deterministic hash (for linking without exposure)
    SUPPRESS = "suppress"  # Remove entirely from text


@dataclass(frozen=True)
class EntityDisposition:
    """Defines how to handle a specific entity type.
    
    Attributes:
        entity_type: Entity type (e.g., 'PERSON', 'EMAIL', 'DIAGNOSIS')
        action: What to do with this entity
        confidence_threshold: Min confidence to apply action (0.0-1.0)
        parameters: Action-specific parameters (e.g., bucket size for generalize)
        description: Human-readable description
    """
    
    entity_type: str
    action: DispositionAction
    confidence_threshold: float = 0.75
    parameters: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    
    def should_process(self, confidence: float) -> bool:
        """Check if entity should be processed based on confidence."""
        return confidence >= self.confidence_threshold


@dataclass
class DomainProfile:
    """Profile defining entity handling for a specific domain/use case.
    
    A profile declares:
    - Which entities to keep (domain-relevant)
    - Which entities to redact/pseudonymize (sensitive)
    - How to handle each entity type
    - Domain-specific recognizers to enable
    - Overall risk posture
    
    Attributes:
        name: Profile name (e.g., 'healthcare', 'finance')
        dispositions: Map of entity_type → EntityDisposition
        defensive_cleanup_enabled: Enable multi-pass PII cleanup
        token_scope: Scope used for consistent token reuse. One of:
            - "thread": same thread only
            - "case": same case across threads
            - "tenant": same tenant across all cases/threads
        entity_similarity_threshold: Threshold for entity matching (0.0-1.0)
        linguistic_filter_enabled: Enable NLP-based false positive filtering
        domain_recognizers: List of domain-specific recognizers to enable
        description: Human-readable description
    """
    
    name: str
    dispositions: dict[str, EntityDisposition] = field(default_factory=dict)
    defensive_cleanup_enabled: bool = True
    token_scope: str = "tenant"
    entity_similarity_threshold: float = 0.75
    linguistic_filter_enabled: bool = True
    domain_recognizers: list[str] = field(default_factory=list)
    description: str = ""

    def __post_init__(self) -> None:
        valid_scopes = {"thread", "case", "tenant"}
        if self.token_scope not in valid_scopes:
            raise ValueError(
                f"Invalid token_scope '{self.token_scope}'. "
                f"Choose one of {sorted(valid_scopes)}"
            )
    
    def get_disposition(self, entity_type: str) -> EntityDisposition | None:
        """Get disposition for entity type, or None if not defined."""
        return self.dispositions.get(entity_type)
    
    def add_disposition(self, disposition: EntityDisposition) -> None:
        """Add or override entity disposition."""
        self.dispositions[disposition.entity_type] = disposition
    
    def should_keep(self, entity_type: str) -> bool:
        """Check if entity type should be kept (domain-relevant)."""
        disposition = self.get_disposition(entity_type)
        return disposition is not None and disposition.action == DispositionAction.KEEP
    
    def should_redact(self, entity_type: str) -> bool:
        """Check if entity type should be redacted."""
        disposition = self.get_disposition(entity_type)
        return disposition is not None and disposition.action == DispositionAction.REDACT
    
    def should_pseudonymize(self, entity_type: str) -> bool:
        """Check if entity type should be pseudonymized."""
        disposition = self.get_disposition(entity_type)
        return disposition is not None and disposition.action == DispositionAction.PSEUDONYMIZE
    
    def list_kept_entities(self) -> list[str]:
        """List all entity types that will be kept."""
        return [
            entity_type
            for entity_type, disp in self.dispositions.items()
            if disp.action == DispositionAction.KEEP
        ]
    
    def list_sensitive_entities(self) -> list[str]:
        """List all entity types that will be anonymized (not kept)."""
        return [
            entity_type
            for entity_type, disp in self.dispositions.items()
            if disp.action != DispositionAction.KEEP
        ]
    
    @classmethod
    def from_dict(cls, config: dict) -> "DomainProfile":
        """Create profile from configuration dictionary.
        
        Format:
        {
            "name": "healthcare",
            "description": "Healthcare domain profile",
            "dispositions": {
                "PERSON": {"action": "pseudonymize", "confidence_threshold": 0.8},
                "DIAGNOSIS": {"action": "keep"},
                "EMAIL": {"action": "redact"}
            }
        }
        """
        dispositions = {}
        for entity_type, disp_config in config.get("dispositions", {}).items():
            action = DispositionAction(disp_config.get("action", "redact"))
            dispositions[entity_type] = EntityDisposition(
                entity_type=entity_type,
                action=action,
                confidence_threshold=disp_config.get("confidence_threshold", 0.75),
                parameters=disp_config.get("parameters", {}),
                description=disp_config.get("description", ""),
            )
        
        return cls(
            name=config["name"],
            dispositions=dispositions,
            defensive_cleanup_enabled=config.get("defensive_cleanup_enabled", True),
            token_scope=config.get("token_scope", "tenant"),
            entity_similarity_threshold=config.get("entity_similarity_threshold", 0.75),
            linguistic_filter_enabled=config.get("linguistic_filter_enabled", True),
            domain_recognizers=config.get("domain_recognizers", []),
            description=config.get("description", ""),
        )
    
    def to_dict(self) -> dict:
        """Export profile to configuration dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "defensive_cleanup_enabled": self.defensive_cleanup_enabled,
            "token_scope": self.token_scope,
            "entity_similarity_threshold": self.entity_similarity_threshold,
            "linguistic_filter_enabled": self.linguistic_filter_enabled,
            "domain_recognizers": self.domain_recognizers,
            "dispositions": {
                entity_type: {
                    "action": disp.action.value,
                    "confidence_threshold": disp.confidence_threshold,
                    "parameters": disp.parameters,
                    "description": disp.description,
                }
                for entity_type, disp in self.dispositions.items()
            },
        }
