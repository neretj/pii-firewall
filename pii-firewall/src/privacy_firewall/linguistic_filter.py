"""Linguistic post-processing to filter false positives from entity detection.

This module provides context-aware filtering using NLP features to reduce
false positives from Presidio and other detectors, without hardcoding keywords.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from .types import Entity


class NLPEngineProtocol(Protocol):
    """Protocol for NLP engines that provide linguistic analysis."""
    
    def has_verb_at_start(self, text: str, start_pos: int, end_pos: int) -> bool:
        """Check if entity starts with a verb (e.g., 'Compare Ana' - 'Compare' is a verb)."""
        ...
    
    def is_likely_name(self, text: str) -> bool:
        """Use POS tags and dependency parsing to validate if text is a name."""
        ...
    
    def get_language(self, text: str) -> str:
        """Detect the language of the text."""
        ...
    
    def trim_non_name_tokens(self, text: str, start_pos: int, end_pos: int) -> tuple[int, int]:
        """Trim non-name tokens from entity boundaries using POS tagging."""
        ...


def create_linguistic_filter(spacy_nlp):
    """Factory function to create a linguistic filter from a spaCy model.
    
    Args:
        spacy_nlp: A loaded spaCy Language object
        
    Returns:
        LinguisticFilter if model supports required features, None otherwise
    """
    # Check if model has POS tagging capability
    test_doc = spacy_nlp("Test sentence")
    has_pos = any(token.pos_ and token.pos_ != "" for token in test_doc)
    
    if not has_pos:
        # Model doesn't support POS tagging (e.g., xx_ent_wiki_sm)
        # Return None to disable filtering gracefully
        return None
    
    engine = SpaCyNLPEngine(spacy_nlp)
    return LinguisticFilter(nlp_engine=engine, enabled=True)


@dataclass
class SpaCyNLPEngine:
    """spaCy-based NLP engine for linguistic analysis.
    
    This reuses an already-loaded spaCy model from Presidio,
    so there's no additional memory overhead.
    """
    
    nlp_model: any  # spaCy Language object
    
    def __post_init__(self) -> None:
        self._nlp = self.nlp_model
        if self._nlp is None:
            raise ValueError("SpaCyNLPEngine requires a loaded spaCy model")

    @staticmethod
    def _is_abbrev_like(token_text: str) -> bool:
        """Return True for short honorific-style abbreviations like 'Dr.' or 'Dra.'."""
        raw = token_text.strip()
        if not raw.endswith("."):
            return False
        stem = raw[:-1]
        if not stem:
            return False
        return bool(re.fullmatch(r"[A-Za-z]{1,4}", stem))
    
    def has_verb_at_start(self, text: str, start_pos: int, end_pos: int) -> bool:
        """Check if the entity starts with or is preceded by a verb.
        
        Example: "Compare Ana Garcia" - "Compare" is a verb before "Ana Garcia".
        This helps filter command phrases like "Compare X", "Check Y", etc.
        
        Also catches cases like "Ana G. vino" where verb is inside entity.
        """
        if not self._nlp:
            return False
        
        # Parse a context window that includes possible verbs before the entity
        context_start = max(0, start_pos - 30)
        context_end = min(len(text), end_pos + 10)
        context_text = text[context_start:context_end]
        
        doc = self._nlp(context_text)
        
        # Calculate entity boundaries within context
        entity_start_in_context = start_pos - context_start
        entity_end_in_context = end_pos - context_start
        
        # Find tokens in or immediately before the entity
        entity_tokens = []
        pre_entity_tokens = []
        
        for token in doc:
            token_start = token.idx
            token_end = token.idx + len(token.text)
            
            # Token is within entity
            if token_start >= entity_start_in_context and token_end <= entity_end_in_context:
                entity_tokens.append(token)
            # Token is within 2 chars before entity (handles spacing)
            elif token_end <= entity_start_in_context and token_end >= entity_start_in_context - 2:
                pre_entity_tokens.append(token)
        
        # Check if entity starts with a verb or function word
        if entity_tokens and entity_tokens[0].pos_ in {"VERB", "AUX", "ADV"}:
            return True
        
        # Check if entity ENDS with a verb (e.g., "Ana G. vino")
        # This catches cases where NER incorrectly includes the verb
        if entity_tokens and entity_tokens[-1].pos_ in {"VERB", "AUX"}:
            return True
        
        # Check if there's a verb immediately before the entity
        if pre_entity_tokens:
            last_before = pre_entity_tokens[-1]
            if last_before.pos_ in {"VERB", "AUX"}:
                return True
        
        return False
    
    def is_likely_name(self, text: str) -> bool:
        """Use linguistic features to validate if text is likely a person name.
        
        Uses POS tagging and dependency parsing (no hardcoded keywords).
        Language-agnostic approach that works for any language with spaCy model.
        
        Conservative approach: only reject if we're CERTAIN it's not a name.
        For privacy, false positives (over-anonymizing) are better than
        false negatives (leaking PII).
        """
        if not self._nlp:
            return True  # Default to keeping entity if NLP unavailable
        
        doc = self._nlp(text)
        tokens = list(doc)
        
        if not tokens:
            return False
        
        # Reject if starts with function words (not content words)
        # These are universally NOT names across all languages
        NON_NAME_POS = {
            "VERB",   # verbs: vino, dice, pregunta (ES), came, said (EN)
            "AUX",    # auxiliary: está, tiene (ES), is, has (EN)
            "ADV",    # adverbs: también, aquí (ES), also, here (EN)
            "CONJ", "CCONJ", "SCONJ",  # conjunctions: y, con, que (ES), and, with (EN)
            "DET",    # determiners: el, la (ES), the, a (EN)
            "ADP",    # prepositions: de, en, con (ES), of, in, with (EN)
            "PART",   # particles: no, sí (ES), not, yes (EN)
            "INTJ",   # interjections: oh, ah
        }
        
        if tokens[0].pos_ in NON_NAME_POS:
            return False
        
        # Reject if contains punctuation that suggests it's not a name
        # Exception: allow periods in abbreviations (A., Dr.)
        for token in tokens:
            if token.pos_ != "PUNCT":
                continue
            if token.text in {".", "'", "-"}:
                continue
            if self._is_abbrev_like(token.text):
                continue
            # Some models label abbreviations as punctuation tokens (e.g., "Dra.").
            # Keep them if they look like short title abbreviations.
            if token.i == 0 and len(tokens) > 1 and self._is_abbrev_like(token.text):
                continue
            
            
            
                return False
        
        # Require at least one proper noun (PROPN) for multi-word entities
        # Single-word entities pass if capitalized (could be abbreviated)
        if len(tokens) > 1:
            has_proper_noun = any(token.pos_ == "PROPN" for token in tokens)
            if not has_proper_noun:
                # Multi-word entity without PROPN is likely not a name
                # Exception: all tokens could be NOUN (e.g., "García López" might be NOUN)
                # Accept if all tokens are NOUN or PROPN
                all_nouns = all(token.pos_ in {"NOUN", "PROPN"} for token in tokens 
                               if token.pos_ != "PUNCT")
                if not all_nouns:
                    return False
        
        # Check capitalization - names should be capitalized
        words = text.split()
        if words and not any(word[0].isupper() for word in words if word):
            return False
        
        # Detect if entity contains a verb as ROOT (main verb)
        # Example: "Ana G. vino" → "vino" is ROOT → not a name
        for token in tokens:
            if token.dep_ == "ROOT" and token.pos_ in {"VERB", "AUX"}:
                return False
        
        # Otherwise, conservatively accept it as a potential name
        return True
    
    def get_language(self, text: str) -> str:
        """Detect language of text.
        
        Note: Language detection is not implemented in this version.
        This method exists to satisfy the Protocol interface.
        """
        # Return empty string - not used in current implementation
        return ""
    
    def trim_non_name_tokens(self, text: str, start_pos: int, end_pos: int) -> tuple[int, int]:
        """Trim non-name tokens from entity boundaries using POS tagging.
        
        Removes function words (verbs, adverbs, prepositions) from start/end.
        No hardcoded keywords - purely linguistic analysis.
        
        Args:
            text: Full text
            start_pos: Entity start position
            end_pos: Entity end position
        
        Returns:
            (new_start, new_end) positions after trimming
        """
        if not self._nlp:
            return start_pos, end_pos
        
        entity_text = text[start_pos:end_pos]
        doc = self._nlp(entity_text)
        tokens = list(doc)
        
        if not tokens:
            return start_pos, end_pos
        
        # POS tags to trim from boundaries (function words, not content words)
        TRIM_POS = {"VERB", "AUX", "ADV", "ADP", "DET", "CONJ", "CCONJ", "SCONJ", "PART"}
        
        # Trim from start
        start_idx = 0
        while start_idx < len(tokens) and tokens[start_idx].pos_ in TRIM_POS:
            start_idx += 1
        
        # Trim from end
        end_idx = len(tokens) - 1
        while end_idx >= start_idx and tokens[end_idx].pos_ in TRIM_POS:
            end_idx -= 1
        
        # Nothing left after trimming
        if start_idx > end_idx:
            return start_pos, end_pos  # Return original, will be filtered later

        # Structural contraction: keep the proper-noun core of the entity.
        # This removes context bleed like "hermano Luis García con" -> "Luis García"
        # without using language-specific keywords.
        window = tokens[start_idx : end_idx + 1]
        proper_noun_positions = [i for i, tok in enumerate(window) if tok.pos_ == "PROPN"]

        if proper_noun_positions:
            first_prop = proper_noun_positions[0]
            last_prop = proper_noun_positions[-1]

            # Some language models tag first names as NOUN instead of PROPN
            # (e.g., "Marie Dupont" in certain French parses). Keep one leading
            # capitalized noun token adjacent to the PROPN core.
            if first_prop > 0:
                prev_tok = window[first_prop - 1]
                if prev_tok.pos_ in {"NOUN", "PROPN"} and prev_tok.text and prev_tok.text[0].isupper():
                    first_prop -= 1

            # Optionally keep one abbreviation token right before the first PROPN
            # (e.g., "Dra. Ana García").
            if first_prop > 0 and self._is_abbrev_like(window[first_prop - 1].text):
                first_prop -= 1

            start_idx = start_idx + first_prop
            end_idx = start_idx + (last_prop - first_prop)

            # Keep trailing period if the last token is a short initial (e.g., "G.")
            if end_idx + 1 < len(tokens):
                last_token = tokens[end_idx]
                next_token = tokens[end_idx + 1]
                if len(last_token.text) <= 2 and next_token.text == ".":
                    end_idx += 1
        
        # Calculate new positions
        new_start = start_pos + tokens[start_idx].idx
        new_end = start_pos + tokens[end_idx].idx + len(tokens[end_idx].text)
        
        return new_start, new_end


@dataclass
class LinguisticFilter:
    """Post-process detected entities to filter false positives using NLP.
    
    This provides a language-agnostic approach to filtering, avoiding hardcoded
    keywords or patterns.
    """
    
    nlp_engine: NLPEngineProtocol | None = None
    enabled: bool = True
    
    def __post_init__(self) -> None:
        if self.enabled and self.nlp_engine is None:
            # Try to initialize spaCy engine, fall back to disabled if not available
            try:
                self.nlp_engine = SpaCyNLPEngine()
            except (ImportError, Exception):
                self.enabled = False
    
    def filter_entities(self, entities: list[Entity], text: str) -> list[Entity]:
        """Filter entities using linguistic analysis.
        
        Args:
            entities: List of detected entities
            text: Original text containing the entities
            
        Returns:
            Filtered list of entities with false positives removed
        """
        if not self.enabled or not self.nlp_engine:
            return entities
        
        filtered = []
        for entity in entities:
            if self._should_keep_entity(entity, text):
                filtered.append(entity)
        
        return filtered
    
    def _should_keep_entity(self, entity: Entity, text: str) -> bool:
        """Determine if entity should be kept or filtered out.
        
        Returns:
            True if entity should be kept, False if it's a false positive
        """
        if not self.nlp_engine:
            return True
        
        # Only apply linguistic filtering to PERSON entities
        # Other types (EMAIL, PHONE, DNI) are regex-based and reliable
        if entity.entity_type != "PERSON":
            return True
        
        # Filter 1: Check if entity starts with a verb (e.g., "Compare Ana Garcia")
        # This is the PRIMARY filter for command phrases
        if self.nlp_engine.has_verb_at_start(text, entity.start, entity.end):
            return False
        
        # Filter 2: Length heuristics (avoid single-word names that might be common words)
        words = entity.text.split()
        if len(words) == 1 and len(entity.text) < 3:
            return False
        
        # Filter 3: Validate if text is actually a name using POS tags
        # BUT: Be conservative - only filter if we're SURE it's not a name
        # False negatives (missing a name) are worse than false positives for privacy
        if not self.nlp_engine.is_likely_name(entity.text):
            return False
        
        return True


# Lightweight fallback filter that doesn't require spaCy
@dataclass
class HeuristicFilter:
    """Fallback filter using pattern-based heuristics when NLP is unavailable.
    
    This is less accurate than linguistic filtering but provides basic protection.
    """
    
    def filter_entities(self, entities: list[Entity], text: str) -> list[Entity]:
        """Filter entities using heuristic patterns."""
        filtered = []
        for entity in entities:
            if self._should_keep_entity(entity, text):
                filtered.append(entity)
        return filtered
    
    def _should_keep_entity(self, entity: Entity, text: str) -> bool:
        """Basic heuristic checks."""
        if entity.entity_type != "PERSON":
            return True
        
        # Check if entity text contains verb indicators (very basic)
        # This is a weak heuristic but better than nothing
        entity_lower = entity.text.lower()
        
        # Ultra-basic verb detection by checking if starts with lowercase
        # (Real verbs in commands are often not capitalized in natural writing)
        # But person names should be capitalized
        words = entity.text.split()
        if words and not words[0][0].isupper():
            return False
        
        # Length check
        if len(words) == 1 and len(entity.text) < 3:
            return False
        
        return True
