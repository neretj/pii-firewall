"""Anonymization engine with disposition-based operators."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, Iterator
from typing import Any

from .types import Entity
from .profiles import DomainProfile, DispositionAction
from .resolver import ContextualEntityResolver
from .vault import MappingVaultProtocol


@dataclass
class AnonymizationResult:
    """Result of anonymization operation."""
    
    text: str
    replacements: list[dict]
    entities_processed: list[Entity]
    entities_kept: list[Entity]


class AnonymizationEngine:
    """Execute anonymization based on domain profile dispositions.
    
    This orchestrates different anonymization strategies per entity type:
    - KEEP: Pass through unchanged
    - REDACT: Replace with [REDACTED] or generic token
    - PSEUDONYMIZE: Replace with reversible token (PERSON_1)
    - GENERALIZE: Replace with coarser value (age 43 → 40-49)
    - MASK: Partial obscurement (card ...1234)
    - HASH: SHA256 hash
    - SUPPRESS: Remove entirely
    """
    
    def __init__(
        self,
        profile: DomainProfile,
        resolver: ContextualEntityResolver,
        vault: MappingVaultProtocol,
        default_ttl_seconds: int = 86400,
    ):
        self.profile = profile
        self.resolver = resolver
        self.vault = vault
        self.default_ttl_seconds = default_ttl_seconds
    
    def anonymize(
        self,
        text: str,
        entities: list[Entity],
        context: dict,
    ) -> AnonymizationResult:
        """Anonymize text based on entity dispositions.
        
        Args:
            text: Original text
            entities: Detected entities (from UnifiedDetectionEngine)
            context: Context dict (tenant_id, case_id, thread_id, actor_id)
        
        Returns:
            AnonymizationResult
        """
        replacements = []
        entities_processed = []
        entities_kept = []
        
        # Sort entities by position (reverse to maintain offsets)
        sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)
        
        anonymized = text
        
        for entity in sorted_entities:
            disposition = self.profile.get_disposition(entity.entity_type)
            
            if disposition is None:
                # No disposition - skip (shouldn't happen after filtering)
                continue
            
            action = disposition.action
            
            if action == DispositionAction.KEEP:
                # Keep as-is
                entities_kept.append(entity)
                continue
            
            # Apply anonymization action
            replacement_text = self._apply_action(
                entity=entity,
                action=action,
                parameters=disposition.parameters,
                context=context,
            )
            
            # Replace in text
            anonymized = anonymized[:entity.start] + replacement_text + anonymized[entity.end:]
            
            # Record replacement
            replacements.append({
                "entity_type": entity.entity_type,
                "source": entity.source,
                "from": entity.text,
                "to": replacement_text,
                "action": action.value,
                "start": entity.start,
                "end": entity.end,
            })
            
            entities_processed.append(entity)
        
        return AnonymizationResult(
            text=anonymized,
            replacements=list(reversed(replacements)),  # Reverse back to original order
            entities_processed=entities_processed,
            entities_kept=entities_kept,
        )
    
    def _apply_action(
        self,
        entity: Entity,
        action: DispositionAction,
        parameters: dict,
        context: dict,
    ) -> str:
        """Apply specific anonymization action to entity."""
        
        if action == DispositionAction.REDACT:
            return self._redact(entity, context, parameters)
        
        elif action == DispositionAction.PSEUDONYMIZE:
            return self._pseudonymize(entity, context, parameters)
        
        elif action == DispositionAction.GENERALIZE:
            return self._generalize(entity, context, parameters)
        
        elif action == DispositionAction.MASK:
            return self._mask(entity, parameters)
        
        elif action == DispositionAction.HASH:
            return self._hash(entity, parameters)
        
        elif action == DispositionAction.SUPPRESS:
            return ""  # Remove entirely
        
        else:
            # Default: redact
            return "[REDACTED]"
    
    def _redact(self, entity: Entity, context: dict, parameters: dict) -> str:
        """Replace with unique reversible token and store mapping.
        
        Note: REDACT now stores mappings for rehydration. Privacy is enforced
        by what the LLM sees (sanitized tokens), not by what we store.
        This ensures users always see their original data back, even if the
        LLM echoes redacted tokens in its response.
        """
        # Use resolver to get unique token (same as PSEUDONYMIZE)
        token = self.resolver.resolve_token(
            tenant_id=context["tenant_id"],
            case_id=context["case_id"],
            thread_id=context["thread_id"],
            entity_type=entity.entity_type,
            value=entity.text,
            token_scope="thread",
        )
        
        # Store in vault for rehydration
        ttl = parameters.get("ttl_seconds", self.default_ttl_seconds)
        self.vault.put(
            context["tenant_id"],
            context["case_id"],
            context["thread_id"],
            token,
            entity.text,
            ttl_seconds=ttl,
        )
        
        return token
    
    def _pseudonymize(self, entity: Entity, context: dict, parameters: dict) -> str:
        """Replace with reversible token and store mapping."""
        # Use resolver to get consistent token
        token = self.resolver.resolve_token(
            tenant_id=context["tenant_id"],
            case_id=context["case_id"],
            thread_id=context["thread_id"],
            entity_type=entity.entity_type,
            value=entity.text,
            token_scope=self.profile.token_scope,
        )
        
        # Store in vault for rehydration
        ttl = parameters.get("ttl_seconds", self.default_ttl_seconds)
        self.vault.put(
            context["tenant_id"],
            context["case_id"],
            context["thread_id"],
            token,
            entity.text,
            ttl_seconds=ttl,
        )
        
        return token
    
    def _generalize(self, entity: Entity, context: dict, parameters: dict) -> str:
        """Replace with unique reversible token and store original value.
        
        Uses unique tokens (like PSEUDONYMIZE) to avoid collisions.
        Stores original value for full rehydration.
        
        Note: Generalization metadata (e.g., age bucket, year-only date) can be
        computed separately for display/logging purposes, but the token itself
        is unique to avoid collisions when multiple entities of the same type
        appear in the conversation.
        """
        # Use resolver to get unique token
        token = self.resolver.resolve_token(
            tenant_id=context["tenant_id"],
            case_id=context["case_id"],
            thread_id=context["thread_id"],
            entity_type=entity.entity_type,
            value=entity.text,
            token_scope="thread",
        )
        
        # Store original value (not generalized form) for full rehydration
        ttl = parameters.get("ttl_seconds", self.default_ttl_seconds)
        self.vault.put(
            context["tenant_id"],
            context["case_id"],
            context["thread_id"],
            token,
            entity.text,  # Store original: "43 años", "today", etc.
            ttl_seconds=ttl,
        )
        
        return token
    
    # Note: Age/date generalization helpers removed - tokens are now unique identifiers
    # Generalization metadata can be computed separately for display/logging if needed
    
    def _mask(self, entity: Entity, parameters: dict) -> str:
        """Partially obscure entity."""
        visible_start = parameters.get("visible_start", 0)
        visible_end = parameters.get("visible_end", 4)
        mask_char = parameters.get("mask_char", "*")
        
        text = entity.text
        
        if len(text) <= visible_start + visible_end:
            # Too short to mask meaningfully
            return mask_char * len(text)
        
        # Show first N and last M characters
        masked_count = len(text) - visible_start - visible_end
        
        result = (
            text[:visible_start] +
            mask_char * masked_count +
            text[-visible_end:] if visible_end > 0 else ""
        )
        
        return result
    
    def _hash(self, entity: Entity, parameters: dict) -> str:
        """Hash entity value (deterministic, non-reversible)."""
        import hashlib
        
        algorithm = parameters.get("algorithm", "sha256")
        salt = parameters.get("salt", "")
        
        value = entity.text + salt
        
        if algorithm == "sha256":
            hash_obj = hashlib.sha256(value.encode())
        elif algorithm == "md5":
            hash_obj = hashlib.md5(value.encode())
        else:
            hash_obj = hashlib.sha256(value.encode())
        
        hash_hex = hash_obj.hexdigest()
        
        # Optionally shorten
        length = parameters.get("length", 16)
        return f"[{entity.entity_type}_HASH_{hash_hex[:length]}]"
    
def rehydrate_text(text: str, mapping: dict[str, str]) -> str:
    """Restore original entities from anonymized text.
    
    Args:
        text: Anonymized text (with tokens like PERSON_1)
        mapping: Map of token → original value
    
    Returns:
        Text with original values restored
    """
    rehydrated = text
    
    # Sort by token length (longest first) to avoid partial replacements
    for token, original in sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True):
        rehydrated = rehydrated.replace(token, original)
    
    return rehydrated


def rehydrate_stream(chunks: Iterable[str], mapping: dict[str, str]) -> Iterator[str]:
    """Restore original entities from streamed anonymized chunks.

    Emits incrementally while preserving correctness when tokens are split
    across chunk boundaries.

    Strategy:
    - Scan the rolling buffer left-to-right for exact token matches.
    - If remaining suffix could be a token prefix, wait for next chunk.
    - Emit only confirmed text/token replacements immediately.
    - Flush remaining tail at the end.
    """
    if not mapping:
        for chunk in chunks:
            yield str(chunk)
        return

    tokens = sorted(mapping.keys(), key=len, reverse=True)
    buffer = ""

    for chunk in chunks:
        buffer += str(chunk)

        emitted: list[str] = []
        idx = 0

        while idx < len(buffer):
            token_match: str | None = None
            for token in tokens:
                if buffer.startswith(token, idx):
                    token_match = token
                    break

            if token_match is not None:
                emitted.append(mapping[token_match])
                idx += len(token_match)
                continue

            remaining = buffer[idx:]
            if any(token.startswith(remaining) for token in tokens):
                # Wait for more chunks to complete potential token match.
                break

            emitted.append(buffer[idx])
            idx += 1

        if emitted:
            yield "".join(emitted)

        buffer = buffer[idx:]

    if buffer:
        yield rehydrate_text(buffer, mapping)
