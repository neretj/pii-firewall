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

    Actions:
    - KEEP:         Pass through unchanged (domain-relevant data).
    - PSEUDONYMIZE: Replace with a reversible token stored in the vault
                    (e.g. [PERSON_001]).  Scope is set by profile.token_scope.
    - GENERALIZE:   Reduce precision (age 43 → 40-49, date → year/month).
                    One-way — no vault entry.
    - MASK:         Partial obscurement (card 4111…1111 → ****1111).
                    One-way.
    - HASH:         SHA-256 hex string — for analytics join-keys, not LLM use.
    - REDACT:       Irreversible removal — entity deleted from text entirely.
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

        if action == DispositionAction.PSEUDONYMIZE:
            return self._pseudonymize(entity, context, parameters)

        elif action == DispositionAction.GENERALIZE:
            return self._generalize(entity, context, parameters)

        elif action == DispositionAction.MASK:
            return self._mask(entity, parameters)

        elif action == DispositionAction.HASH:
            return self._hash(entity, parameters)

        elif action == DispositionAction.REDACT:
            return ""  # Irreversible removal — entity deleted from text entirely

        else:
            # Fallback: pseudonymize
            return self._pseudonymize(entity, context, parameters)
    
    def _pseudonymize(self, entity: Entity, context: dict, parameters: dict) -> str:
        """Replace with a reversible placeholder token and store the mapping in the vault.

        Token scope (thread / case / tenant) is governed by the profile's
        ``token_scope`` field — not by the action name.  All cross-session /
        cross-thread consistency decisions belong to the caller via context.
        """
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
        """Replace entity with a coarsened/generalized representation.

        GENERALIZE is intentionally one-way: the coarsened value (e.g., an age
        range or a year) is the final form seen by the LLM and the end user.
        No vault entry is created — there is nothing to rehydrate.

        Dispatch rules:
          - AGE / DATE_TIME that looks like an age → decade bucket (43 → 40-49)
          - DATE / DATE_TIME that looks like a calendar date → year or month/year
          - LOCATION → handled by caller (city-level generalization; falls back
            to a numbered token when geocoding is not available)
          - Everything else → numbered token stored in vault (same as REDACT)
        """
        entity_type = entity.entity_type
        text = entity.text

        if entity_type == "AGE":
            return self._generalize_age(text, parameters)

        if entity_type in ("DATE", "DATE_TIME"):
            granularity = parameters.get("granularity") or parameters.get("level", "year")
            result = self._generalize_date(text, granularity)
            if result is not None:
                return result
            # Text looks like an age ("43 years old", "43 años") — treat as age
            age_result = self._generalize_age(text, {})
            if age_result != "[AGE]":
                return age_result

        # Fall back: numbered token + vault (covers LOCATION and unknown types)
        token = self.resolver.resolve_token(
            tenant_id=context["tenant_id"],
            case_id=context["case_id"],
            thread_id=context["thread_id"],
            entity_type=entity_type,
            value=text,
            token_scope=self.profile.token_scope,
        )
        ttl = parameters.get("ttl_seconds", self.default_ttl_seconds)
        self.vault.put(
            context["tenant_id"],
            context["case_id"],
            context["thread_id"],
            token,
            text,
            ttl_seconds=ttl,
        )
        return token

    def _generalize_age(self, text: str, parameters: dict) -> str:
        """Return decade bucket for an age value, e.g., 43 → '40-49'."""
        import re
        m = re.search(r"\b(\d{1,3})\b", text)
        if not m:
            return "[AGE]"
        age = int(m.group(1))
        if not (0 <= age <= 130):
            return "[AGE]"
        bucket_size = parameters.get("bucket_size", 10)
        low = (age // bucket_size) * bucket_size
        high = low + bucket_size - 1
        return f"{low}-{high}"

    def _generalize_date(self, text: str, granularity: str) -> str | None:
        """Reduce date precision to year or month/year.

        Returns None when the text does not contain a recognisable calendar date
        (so the caller can try other generalization strategies).
        """
        import re
        import calendar as cal

        # Must contain a 4-digit year in the range 1900-2099
        m = re.search(r"\b((?:19|20)\d{2})\b", text)
        if not m:
            return None
        year = m.group(1)

        if granularity == "year":
            return year

        # ── month/year ────────────────────────────────────────────────────
        month_map: dict[str, int] = {
            # English
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12,
            # Spanish
            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
            "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
            "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
            # French
            "janvier": 1, "février": 2, "mars": 3, "avril": 4,
            "mai": 5, "juin": 6, "juillet": 7, "août": 8,
            "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12,
            # German
            "januar": 1, "februar": 2, "märz": 3,
            "juni": 6, "juli": 7, "september": 9, "oktober": 10, "dezember": 12,
            # Italian
            "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4,
            "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8,
            "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
            # Portuguese
            "janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4,
            "junho": 6, "julho": 7, "setembro": 9, "outubro": 10, "dezembro": 12,
        }
        text_lower = text.lower()
        for name, num in month_map.items():
            if name in text_lower:
                return f"{cal.month_abbr[num]} {year}"

        # Numeric: YYYY-MM[-DD]
        m2 = re.search(r"(?:19|20)\d{2}[/\-\.](\d{1,2})", text)
        if m2:
            num = int(m2.group(1))
            if 1 <= num <= 12:
                return f"{cal.month_abbr[num]} {year}"

        # Numeric: DD/MM/YYYY or MM/DD/YYYY — assume DD/MM (European)
        m3 = re.search(r"(\d{1,2})[/\-\.](\d{1,2})[/\-\.](?:19|20)\d{2}", text)
        if m3:
            num = int(m3.group(2))
            if 1 <= num <= 12:
                return f"{cal.month_abbr[num]} {year}"

        return year  # year-only fallback
    
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
