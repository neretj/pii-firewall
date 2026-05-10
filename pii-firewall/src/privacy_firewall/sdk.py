from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterator
from typing import Any

from .firewall import PrivacyFirewall, create_firewall
from .types import ProcessResult
from .profiles import DomainProfile


def _walk_payload(value: Any, transform) -> Any:
    if isinstance(value, str):
        return transform(value)
    if isinstance(value, list):
        return [_walk_payload(item, transform) for item in value]
    if isinstance(value, dict):
        return {k: _walk_payload(v, transform) for k, v in value.items()}
    return value


@dataclass
class PrivacyFirewallSDK:
    """High-level provider-agnostic SDK facade.

    This class is intentionally minimal: sanitize before outbound model calls,
    then rehydrate model outputs using vault mappings.
    """

    firewall: PrivacyFirewall

    @classmethod
    def create(
        cls,
        *,
        domain: str = "generic",
        preset: str | None = None,
        profile: DomainProfile | None = None,
        language: str | None = None,
        detector_backend: str = "regex",
        **kwargs,
    ) -> "PrivacyFirewallSDK":
        selected = preset or domain
        return cls(
            firewall=create_firewall(
                domain=selected,
                profile=profile,
                language=language,
                detector_backend=detector_backend,
                **kwargs,
            )
        )

    def anonymize_text(self, *, text: str, context: dict) -> ProcessResult:
        return self.firewall.anonymize(text=text, context=context)

    def rehydrate_text(self, *, text: str, context: dict, mapping: dict[str, str] | None = None) -> str:
        return self.firewall.rehydrate(text=text, context=context, mapping=mapping)

    def get_mapping(self, *, context: dict) -> dict[str, str]:
        return self.firewall.get_mapping(context=context)

    def secure_call(
        self,
        *,
        text: str,
        context: dict,
        llm_client: Any,
        mapping: dict[str, str] | None = None,
    ) -> ProcessResult:
        return self.firewall.secure_call(
            text=text,
            context=context,
            llm_client=llm_client,
            mapping=mapping,
        )

    def secure_call_stream(
        self,
        *,
        text: str,
        context: dict,
        llm_client: Any,
        mapping: dict[str, str] | None = None,
    ) -> Iterator[str]:
        return self.firewall.secure_call_stream(
            text=text,
            context=context,
            llm_client=llm_client,
            mapping=mapping,
        )

    def anonymize_payload(self, *, payload: Any, context: dict) -> Any:
        return _walk_payload(payload, lambda s: self.anonymize_text(text=s, context=context).sanitized_text)

    def rehydrate_payload(
        self,
        *,
        payload: Any,
        context: dict,
        mapping: dict[str, str] | None = None,
    ) -> Any:
        return _walk_payload(payload, lambda s: self.rehydrate_text(text=s, context=context, mapping=mapping))

    def forget(self, *, tenant_id: str, case_id: str, thread_id: str) -> int:
        return self.firewall.forget(tenant_id=tenant_id, case_id=case_id, thread_id=thread_id)