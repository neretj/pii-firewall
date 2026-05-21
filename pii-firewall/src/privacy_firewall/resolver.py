from __future__ import annotations

import re
from dataclasses import dataclass, field


def _normalize_name(value: str) -> str:
    """Normalize name for comparison: lowercase alphanumeric + spaces.
    
    Removes professional titles without hardcoded keywords by detecting:
    - Short abbreviations at start (Dr., Dra., Sr., Prof., etc.)
    - Pattern: 1-4 letters followed by period at beginning
    """
    # Strip and split into words
    value_stripped = value.strip()
    words = value_stripped.split()
    
    if not words:
        return ""
    
    # Remove title-like patterns from start (short abbreviations with period)
    # Examples: "Dr.", "Dra.", "Prof.", "Sr.", "Sra.", "Mr.", "Mrs.", "Ms."
    # Pattern: 1-4 alphabetic chars + period, OR single word <= 4 chars at start
    while words:
        first_word = words[0]
        
        # Check if it's a title pattern:
        # - Ends with period and is short (1-4 chars before period)
        # - Is a short word (1-4 chars total) at the beginning
        is_title_abbrev = first_word.endswith('.') and len(first_word.rstrip('.')) <= 4
        is_short_prefix = len(first_word) <= 4 and len(words) > 1
        
        if is_title_abbrev:
            words.pop(0)
        elif is_short_prefix and first_word.isalpha():
            # Could be title without period (Dr, Sr) - only remove if followed by longer word
            if len(words) > 1 and len(words[1]) > 4:
                words.pop(0)
            else:
                break
        else:
            break
    
    # Reconstruct without titles
    cleaned = " ".join(words)
    
    # Normalize to lowercase alphanumeric + spaces
    return "".join(ch.lower() for ch in cleaned if ch.isalnum() or ch.isspace()).strip()


def _levenshtein(a: str, b: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def _is_abbreviation_match(abbrev: str, full: str) -> bool:
    """Check if abbrev is an abbreviation of full name.
    
    Examples:
        - "Ana G." matches "Ana Garcia"
        - "A. Garcia" matches "Ana Garcia"
        - "Ana" matches "Ana Garcia"
    """
    abbrev = abbrev.strip()
    full = full.strip()
    
    # Split into parts
    abbrev_parts = [p.strip().rstrip('.') for p in abbrev.split()]
    full_parts = full.split()
    
    if len(abbrev_parts) > len(full_parts):
        return False
    
    # Check if each abbreviated part matches a full part
    for i, abbrev_part in enumerate(abbrev_parts):
        if i >= len(full_parts):
            return False
        
        full_part = full_parts[i]
        
        # Exact match
        if abbrev_part.lower() == full_part.lower():
            continue
        
        # Initial match (e.g., "A" matches "Ana")
        if len(abbrev_part) == 1 and full_part.lower().startswith(abbrev_part.lower()):
            continue
        
        # Prefix match (e.g., "An" matches "Ana")
        if full_part.lower().startswith(abbrev_part.lower()):
            continue
        
        return False
    
    return True


def _extract_initials(name: str) -> str:
    """Extract initials from a name.
    
    Example: "Ana Garcia" -> "ag"
    """
    parts = name.split()
    return "".join(p[0].lower() for p in parts if p)


def _similarity_score(a: str, b: str) -> float:
    """Calculate similarity score between two names (0.0 to 1.0).
    
    Uses multiple signals:
    - Levenshtein distance
    - Abbreviation matching
    - Initial matching
    - Common tokens
    """
    a_norm = _normalize_name(a)
    b_norm = _normalize_name(b)
    
    # Exact match
    if a_norm == b_norm:
        return 1.0
    
    # Levenshtein-based similarity
    max_len = max(len(a_norm), len(b_norm))
    if max_len == 0:
        return 0.0
    
    lev_distance = _levenshtein(a_norm, b_norm)
    lev_similarity = 1.0 - (lev_distance / max_len)
    
    # Check abbreviation match
    abbrev_score = 0.0
    if _is_abbreviation_match(a, b) or _is_abbreviation_match(b, a):
        abbrev_score = 0.9
    
    # Check initial match
    initial_score = 0.0
    a_initials = _extract_initials(a_norm)
    b_initials = _extract_initials(b_norm)
    if a_initials == b_initials and len(a_initials) >= 2:
        initial_score = 0.7
    
    # Token overlap (for multi-word names)
    a_tokens = set(a_norm.split())
    b_tokens = set(b_norm.split())
    if a_tokens and b_tokens:
        common_tokens = a_tokens & b_tokens
        token_overlap = len(common_tokens) / max(len(a_tokens), len(b_tokens))
        # Boost if there's significant overlap
        if token_overlap > 0.5:
            lev_similarity = max(lev_similarity, token_overlap)
    
    # Return the highest score from all methods
    return max(lev_similarity, abbrev_score, initial_score)


@dataclass
class ContextualEntityResolver:
    """Advanced entity resolver with fuzzy matching and abbreviation support.
    
    Features:
    - Handles typos using Levenshtein distance
    - Matches abbreviations (e.g., "Ana G." → "Ana Garcia")
    - Tracks entity continuity across conversation turns
    - Configurable similarity thresholds
    """
    
    # key: (tenant, scope, entity_type) -> token -> canonical
    memory: dict[tuple[str, str, str], dict[str, str]] = field(default_factory=dict)
    
    # Similarity threshold for matching (0.0 to 1.0)
    # Higher = stricter matching, Lower = more fuzzy matching
    similarity_threshold: float = 0.75

    def resolve_token(
        self,
        *,
        tenant_id: str,
        case_id: str,
        thread_id: str,
        entity_type: str,
        value: str,
        token_scope: str = "tenant",
    ) -> str:
        """Resolve an entity value to its canonical token.
        
        If the value matches an existing entity (by similarity), returns
        the existing token. Otherwise, creates a new token.
        """
        if token_scope == "thread":
            scope = f"thread:{thread_id}"
        elif token_scope == "case":
            scope = f"case:{case_id}"
        elif token_scope == "tenant":
            scope = "tenant:*"
        else:
            raise ValueError(
                f"Invalid token_scope '{token_scope}'. "
                "Choose one of ['thread', 'case', 'tenant']"
            )

        key = (tenant_id, scope, entity_type)
        if key not in self.memory:
            self.memory[key] = {}

        # For PERSON entities use fuzzy matching so that "John Smith", "J. Smith"
        # and "JOHN SMITH" all map to the same pseudonym.
        # For every other entity type (EMAIL, IBAN, SSN, phone, …) use exact
        # matching only — structurally similar values (e.g. john.doe@ vs
        # jane.doe@) must never share a token.
        if entity_type == "PERSON":
            canonical = _normalize_name(value)
            best_match = None
            best_score = 0.0
            for token, known in self.memory[key].items():
                score = _similarity_score(canonical, known)
                if score > best_score and score >= self.similarity_threshold:
                    best_score = score
                    best_match = token
            if best_match:
                return best_match
        else:
            canonical = value.lower().strip()
            for token, known in self.memory[key].items():
                if known == canonical:
                    return token

        # No match found, create new token.
        # Use square brackets because LLM outputs and report templates
        # tend to preserve this delimiter more consistently than angle brackets.
        token = f"[{entity_type}_{len(self.memory[key]) + 1:03d}]"
        self.memory[key][token] = canonical
        return token
