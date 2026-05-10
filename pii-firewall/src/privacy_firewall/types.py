from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Entity:
    text: str
    entity_type: str
    start: int
    end: int
    confidence: float
    source: str


@dataclass
class TraceRecord:
    trace_id: str
    tenant_id: str
    case_id: str
    policy_mode: str
    detected_entities: list[dict[str, Any]] = field(default_factory=list)
    replacements: list[dict[str, Any]] = field(default_factory=list)
    blocked: bool = False
    block_reason: str | None = None
    cleanup_warnings: list[str] = field(default_factory=list)
    language: str = "unknown"  # Detected language
    entities_kept: list[dict[str, Any]] = field(default_factory=list)  # Entities kept (domain-relevant)


@dataclass
class ProcessResult:
    sanitized_text: str
    model_output: str
    final_text: str
    trace: TraceRecord
