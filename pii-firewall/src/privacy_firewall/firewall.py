from __future__ import annotations

import re
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from .anonymization_engine import AnonymizationEngine, rehydrate_text, rehydrate_stream
from .cleanup_utils import apply_residual_cleanup, has_residual_pii
from .language import LanguageDetector, LanguageRouter, ThreadLanguageCache
from .llm import call_model, stream_model
from .patterns import EntityPattern, PatternCatalog, create_default_catalog
from .profiles import DispositionAction, DomainProfile, EntityDisposition
from .resolver import ContextualEntityResolver
from .types import ProcessResult, TraceRecord
from .unified_detector import UnifiedDetectionEngine
from .vault import InMemoryMappingVault, MappingVaultProtocol


def apply_defensive_cleanup(text: str, max_iterations: int = 3) -> tuple[str, list[dict], list[str]]:
    current_text = text
    all_replacements: list[dict] = []
    warnings: list[str] = []

    for iteration in range(max_iterations):
        if not has_residual_pii(current_text):
            break

        cleaned, replacements = apply_residual_cleanup(current_text)

        if not replacements:
            warnings.append(
                f"Iteration {iteration + 1}: Residual PII detected but no known patterns matched. "
                "This may indicate a new PII type requiring detector updates."
            )
            break

        all_replacements.extend(replacements)
        current_text = cleaned

    if has_residual_pii(current_text):
        warnings.append(
            f"After {max_iterations} cleanup passes, residual PII patterns still detected. "
            "Proceeding with best-effort anonymization. Review detector coverage."
        )

    return current_text, all_replacements, warnings


@dataclass
class PrivacyFirewallV2:
    profile: DomainProfile
    vault: MappingVaultProtocol | None = None
    llm_client: Any = None
    resolver: ContextualEntityResolver | None = None
    language_detector: LanguageDetector | None = None
    language_cache: ThreadLanguageCache | None = None
    language_router: LanguageRouter | None = None
    pattern_catalog: PatternCatalog | None = None

    detector_backend: str = "regex"
    custom_recognizers: list[Any] = None
    transformer_model_id: str | None = None
    transformer_device: int = -1
    gliner_model_id: str = "knowledgator/gliner-pii-base-v1.0"
    opf_checkpoint: str | None = None

    manual_language: str | None = None
    enable_defensive_cleanup: bool = True

    def __post_init__(self) -> None:
        if self.vault is None:
            self.vault = InMemoryMappingVault()

        if self.resolver is None:
            self.resolver = ContextualEntityResolver(
                similarity_threshold=self.profile.entity_similarity_threshold
            )

        if self.language_detector is None:
            try:
                self.language_detector = LanguageDetector()
            except ImportError:
                if self.manual_language is None:
                    raise ImportError(
                        "langdetect is required for auto language detection. "
                        "Install with: pip install 'pii-firewall[langdetect]' "
                        "or provide manual_language parameter"
                    )
                self.language_detector = None

        if self.language_cache is None:
            self.language_cache = ThreadLanguageCache()

        if self.language_router is None:
            self.language_router = LanguageRouter()

        if self.pattern_catalog is None:
            self.pattern_catalog = create_default_catalog()

        if self.custom_recognizers is None:
            self.custom_recognizers = []

        self._detection_engine = UnifiedDetectionEngine(
            profile=self.profile,
            language_detector=self.language_detector,
            language_cache=self.language_cache,
            language_router=self.language_router,
            pattern_catalog=self.pattern_catalog,
            detector_backend=self.detector_backend,
            custom_recognizers=self.custom_recognizers,
            transformer_model_id=self.transformer_model_id,
            transformer_device=self.transformer_device,
            gliner_model_id=self.gliner_model_id,
            opf_checkpoint=self.opf_checkpoint,
        )

        self._anonymization_engine = AnonymizationEngine(
            profile=self.profile,
            resolver=self.resolver,
            vault=self.vault,
        )

    def anonymize(self, *, text: str, context: dict) -> ProcessResult:
        self._validate_context(context)

        trace = TraceRecord(
            trace_id=str(uuid.uuid4()),
            tenant_id=context["tenant_id"],
            case_id=context["case_id"],
            policy_mode=self.profile.name,
        )

        entities, detected_language = self._detection_engine.detect(
            text=text,
            language=self.manual_language,
            thread_id=context.get("thread_id"),
            context_words=None,
        )

        trace.language = detected_language
        trace.detected_entities = [
            {
                "entity_type": ent.entity_type,
                "text": ent.text,
                "confidence": ent.confidence,
                "source": ent.source,
                "start": ent.start,
                "end": ent.end,
            }
            for ent in entities
        ]

        anon_result = self._anonymization_engine.anonymize(
            text=text,
            entities=entities,
            context=context,
        )

        trace.replacements = anon_result.replacements
        trace.entities_kept = [
            {"entity_type": ent.entity_type, "text": ent.text}
            for ent in anon_result.entities_kept
        ]

        sanitized_text = anon_result.text

        if self.enable_defensive_cleanup and self.profile.defensive_cleanup_enabled:
            sanitized_text, residual_replacements, cleanup_warnings = apply_defensive_cleanup(sanitized_text)
            if residual_replacements:
                trace.replacements.extend(residual_replacements)
            if cleanup_warnings:
                trace.cleanup_warnings = cleanup_warnings

        return ProcessResult(
            sanitized_text=sanitized_text,
            model_output="",
            final_text="",
            trace=trace,
        )

    def rehydrate(self, *, text: str, context: dict, mapping: dict[str, str] | None = None) -> str:
        self._validate_context(context)
        active_mapping = mapping
        if active_mapping is None:
            active_mapping = self.vault.get_case_mapping(
                context["tenant_id"],
                context["case_id"],
                context["thread_id"],
            )
        return rehydrate_text(text=text, mapping=active_mapping)

    def get_mapping(self, *, context: dict) -> dict[str, str]:
        self._validate_context(context)
        return self.vault.get_case_mapping(
            context["tenant_id"],
            context["case_id"],
            context["thread_id"],
        )

    def secure_call(
        self,
        *,
        text: str,
        context: dict,
        llm_client: Any | None = None,
        mapping: dict[str, str] | None = None,
    ) -> ProcessResult:
        anon_result = self.anonymize(text=text, context=context)
        capsule = self._build_context_capsule(context=context, sanitized_text=anon_result.sanitized_text)
        selected_client = llm_client if llm_client is not None else self.llm_client
        model_output = call_model(selected_client, anon_result.sanitized_text, capsule)
        final_text = self.rehydrate(text=model_output, context=context, mapping=mapping)

        return ProcessResult(
            sanitized_text=anon_result.sanitized_text,
            model_output=model_output,
            final_text=final_text,
            trace=anon_result.trace,
        )

    def secure_call_stream(
        self,
        *,
        text: str,
        context: dict,
        llm_client: Any | None = None,
        mapping: dict[str, str] | None = None,
    ) -> Iterator[str]:
        """Stream rehydrated output chunks for the secure call flow."""
        anon_result = self.anonymize(text=text, context=context)
        capsule = self._build_context_capsule(context=context, sanitized_text=anon_result.sanitized_text)
        selected_client = llm_client if llm_client is not None else self.llm_client

        active_mapping = mapping
        if active_mapping is None:
            active_mapping = self.vault.get_case_mapping(
                context["tenant_id"],
                context["case_id"],
                context["thread_id"],
            )

        model_chunks = stream_model(selected_client, anon_result.sanitized_text, capsule)
        yield from rehydrate_stream(model_chunks, active_mapping)

    def process(self, *, text: str, context: dict) -> ProcessResult:
        return self.secure_call(text=text, context=context)

    def forget(self, *, tenant_id: str, case_id: str, thread_id: str) -> int:
        return self.vault.forget_case(tenant_id, case_id, thread_id)

    def add_custom_pattern(self, pattern: Any) -> None:
        self.pattern_catalog.add_pattern(pattern)

    def add_custom_regex(
        self,
        *,
        entity_type: str,
        regex: str,
        locales: list[str] | None = None,
        confidence: float = 0.95,
        context_words: list[str] | None = None,
        description: str = "",
        disposition_action: str = "redact",
        confidence_threshold: float = 0.75,
        disposition_parameters: dict[str, Any] | None = None,
    ) -> None:
        try:
            action = DispositionAction(disposition_action)
        except ValueError as exc:
            raise ValueError(
                f"Invalid disposition_action '{disposition_action}'. "
                f"Choose one of {[a.value for a in DispositionAction]}"
            ) from exc

        target_locales = locales or ["GLOBAL"]
        compiled = re.compile(regex)

        for locale in target_locales:
            pattern = EntityPattern(
                entity_type=entity_type,
                locale=locale,
                pattern=compiled,
                confidence=confidence,
                context_words=tuple(context_words or []),
                description=description,
            )
            self.pattern_catalog.add_pattern(pattern)

        if self.profile.get_disposition(entity_type) is None:
            self.profile.add_disposition(
                EntityDisposition(
                    entity_type=entity_type,
                    action=action,
                    confidence_threshold=confidence_threshold,
                    parameters=disposition_parameters or {},
                    description=description or f"Custom entity type {entity_type}",
                )
            )

    def add_custom_recognizer(self, recognizer: Any) -> None:
        self.custom_recognizers.append(recognizer)

    def preload_languages(self, languages: list[str]) -> None:
        self.language_router.preload_languages(languages)

    def export_profile(self) -> dict:
        return self.profile.to_dict()

    @staticmethod
    def _validate_context(context: dict) -> None:
        required = {"tenant_id", "case_id", "thread_id", "actor_id"}
        missing = [key for key in required if key not in context]
        if missing:
            raise ValueError(f"Missing context keys: {', '.join(missing)}")

    @staticmethod
    def _build_context_capsule(*, context: dict, sanitized_text: str) -> dict:
        return {
            "tenant_id": context["tenant_id"],
            "case_id": context["case_id"],
            "thread_id": context["thread_id"],
        }


def create_firewall(
    domain: str = "generic",
    profile: DomainProfile | None = None,
    language: str | None = None,
    detector_backend: str = "regex",
    token_scope: str | None = None,
    **kwargs,
) -> PrivacyFirewallV2:
    from .profiles import get_preset_profile

    base_profile = profile if profile is not None else get_preset_profile(domain)
    selected_profile = DomainProfile.from_dict(base_profile.to_dict())

    if token_scope is not None:
        selected_profile.token_scope = token_scope

    return PrivacyFirewallV2(
        profile=selected_profile,
        manual_language=language,
        detector_backend=detector_backend,
        **kwargs,
    )
