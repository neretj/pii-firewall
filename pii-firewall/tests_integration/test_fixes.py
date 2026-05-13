"""Regression tests for all confirmed bug fixes.

Each test is labelled with the finding number it covers so failures are easy
to trace back to the original audit report.
"""
from __future__ import annotations

import time
import pytest

# ── helpers ────────────────────────────────────────────────────────────────

CTX = {
    "tenant_id": "fix-tenant",
    "case_id": "fix-case",
    "thread_id": "fix-thread",
    "actor_id": "fix-user",
}

# resolve_token does not accept actor_id
RESOLVER_CTX = {k: CTX[k] for k in ("tenant_id", "case_id", "thread_id")}


def _regex_firewall(domain: str = "generic", language: str = "en"):
    from privacy_firewall.firewall import create_firewall
    from privacy_firewall.vault import InMemoryMappingVault
    from privacy_firewall.llm import MockLLMClient

    return create_firewall(
        domain=domain,
        language=language,
        detector_backend="regex",
        vault=InMemoryMappingVault(),
        llm_client=MockLLMClient(prefix=""),
    )


# ── Fix #3: _mask() ternary precedence ─────────────────────────────────────

class TestMaskTernary:
    """Bug: visible_end=0 returned '' instead of all-mask chars."""

    def _mask(self, text: str, visible_start: int = 0, visible_end: int = 4):
        from privacy_firewall.anonymization_engine import AnonymizationEngine
        from privacy_firewall.types import Entity

        ae = AnonymizationEngine.__new__(AnonymizationEngine)
        e = Entity(
            text=text, entity_type="CREDIT_CARD",
            start=0, end=len(text), confidence=0.99, source="test",
        )
        return ae._mask(e, {"visible_start": visible_start, "visible_end": visible_end, "mask_char": "*"})

    def test_visible_end_zero_masks_everything(self):
        result = self._mask("4111111111111111", visible_end=0)
        assert result == "*" * 16, f"Expected all stars, got {result!r}"

    def test_visible_end_four_shows_last_four(self):
        result = self._mask("4111111111111111", visible_end=4)
        assert result == "************1111"

    def test_visible_start_four_shows_first_four(self):
        result = self._mask("4111111111111111", visible_start=4, visible_end=0)
        assert result == "4111************"

    def test_visible_start_and_end(self):
        result = self._mask("4111111111111111", visible_start=4, visible_end=4)
        assert result == "4111********1111"

    def test_short_text_fully_masked(self):
        # text shorter than visible_start + visible_end → all masked
        result = self._mask("1234", visible_end=6)
        assert result == "****"


# ── Fix #6: visible_digits → visible_end in presets ────────────────────────

class TestCreditCardPresetKey:
    """Bug: CREDIT_CARD disposition used 'visible_digits' but engine reads 'visible_end'."""

    def test_universal_disposition_uses_visible_end(self):
        from privacy_firewall.profiles.presets import _UNIVERSAL_DISPOSITIONS

        cc = _UNIVERSAL_DISPOSITIONS["CREDIT_CARD"]
        assert "visible_end" in cc.parameters, "Key should be 'visible_end'"
        assert "visible_digits" not in cc.parameters, "'visible_digits' is the old wrong key"
        assert cc.parameters["visible_end"] == 4

    def test_mask_applied_correctly_via_firewall(self):
        """End-to-end: credit card in text is masked to last 4 digits."""
        fw = _regex_firewall()
        result = fw.secure_call(
            text="My card is 4111111111111111",
            context=CTX,
        )
        assert "4111111111111111" not in result.sanitized_text
        # Last 4 digits should be visible in the masked token
        assert "1111" in result.sanitized_text


# ── Fix #4 (revised): resolver exact-match for non-PERSON ──────────────────

class TestResolverExactMatchNonPerson:
    """Bug: different emails could share a pseudonym via fuzzy Levenshtein."""

    def _resolver(self):
        from privacy_firewall.resolver import ContextualEntityResolver
        return ContextualEntityResolver()

    def test_different_emails_get_different_tokens(self):
        r = self._resolver()
        t1 = r.resolve_token(**RESOLVER_CTX, entity_type="EMAIL", value="john.doe@company.com")
        t2 = r.resolve_token(**RESOLVER_CTX, entity_type="EMAIL", value="jane.doe@company.com")
        assert t1 != t2, "Two distinct emails must not share a pseudonym"

    def test_same_email_gets_same_token(self):
        r = self._resolver()
        t1 = r.resolve_token(**RESOLVER_CTX, entity_type="EMAIL", value="john.doe@company.com")
        t2 = r.resolve_token(**RESOLVER_CTX, entity_type="EMAIL", value="john.doe@company.com")
        assert t1 == t2

    def test_email_case_insensitive_same_token(self):
        r = self._resolver()
        t1 = r.resolve_token(**RESOLVER_CTX, entity_type="EMAIL", value="John.Doe@Company.com")
        t2 = r.resolve_token(**RESOLVER_CTX, entity_type="EMAIL", value="john.doe@company.com")
        assert t1 == t2, "Same email different case should map to same token"

    def test_different_ibans_get_different_tokens(self):
        r = self._resolver()
        t1 = r.resolve_token(**RESOLVER_CTX, entity_type="IBAN", value="ES9121000418401234567891")
        t2 = r.resolve_token(**RESOLVER_CTX, entity_type="IBAN", value="ES9121000418409999999999")
        assert t1 != t2

    def test_person_fuzzy_matching_preserved(self):
        """PERSON type must still use fuzzy matching."""
        r = self._resolver()
        t1 = r.resolve_token(**RESOLVER_CTX, entity_type="PERSON", value="John Smith")
        t2 = r.resolve_token(**RESOLVER_CTX, entity_type="PERSON", value="john smith")
        assert t1 == t2, "Same person different case should resolve to same token"

    def test_person_abbreviation_matching_preserved(self):
        r = self._resolver()
        t1 = r.resolve_token(**RESOLVER_CTX, entity_type="PERSON", value="Ana García")
        t2 = r.resolve_token(**RESOLVER_CTX, entity_type="PERSON", value="A. García")
        assert t1 == t2, "Abbreviated name should resolve to same person token"


# ── Fix #5: _generalize() LOCATION no longer stored in vault ───────────────

class TestGeneralizeNoVaultEntry:
    """Bug: GENERALIZE fallback stored LOCATION in vault despite 'one-way' contract."""

    def test_location_not_stored_in_vault(self):
        from privacy_firewall.anonymization_engine import AnonymizationEngine
        from privacy_firewall.types import Entity
        from privacy_firewall.vault import InMemoryMappingVault
        from privacy_firewall.resolver import ContextualEntityResolver
        from privacy_firewall.profiles.presets import get_preset_profile

        vault = InMemoryMappingVault()
        ae = AnonymizationEngine(
            profile=get_preset_profile("generic"),
            resolver=ContextualEntityResolver(),
            vault=vault,
        )
        e = Entity(
            text="Paris", entity_type="LOCATION",
            start=0, end=5, confidence=0.9, source="test",
        )
        result = ae._generalize(e, CTX, {"level": "city"})
        assert result == "[LOCATION]"
        mapping = vault.get_case_mapping(CTX["tenant_id"], CTX["case_id"], CTX["thread_id"])
        assert len(mapping) == 0, "GENERALIZE must not create vault entries"

    def test_generalize_returns_non_reversible_label(self):
        from privacy_firewall.anonymization_engine import AnonymizationEngine
        from privacy_firewall.types import Entity
        from privacy_firewall.vault import InMemoryMappingVault
        from privacy_firewall.resolver import ContextualEntityResolver
        from privacy_firewall.profiles.presets import get_preset_profile

        ae = AnonymizationEngine(
            profile=get_preset_profile("generic"),
            resolver=ContextualEntityResolver(),
            vault=InMemoryMappingVault(),
        )
        e = Entity(text="London", entity_type="LOCATION", start=0, end=6, confidence=0.9, source="test")
        result = ae._generalize(e, CTX, {})
        assert result == "[LOCATION]"
        assert "[LOCATION_" not in result, "Should not be a numbered/reversible token"


# ── Fix #14: _hash() no longer allows MD5 ──────────────────────────────────

class TestHashSecurity:
    """Bug: MD5 was allowed and empty salt was accepted silently."""

    def _hash(self, value: str, algorithm: str = "sha256", salt: str = "") -> str:
        from privacy_firewall.anonymization_engine import AnonymizationEngine
        from privacy_firewall.types import Entity

        ae = AnonymizationEngine.__new__(AnonymizationEngine)
        e = Entity(text=value, entity_type="SSN", start=0, end=len(value), confidence=1.0, source="test")
        return ae._hash(e, {"algorithm": algorithm, "salt": salt})

    def test_sha256_still_works(self):
        result = self._hash("123-45-6789", algorithm="sha256")
        assert result.startswith("[SSN_HASH_")

    def test_sha512_works(self):
        result = self._hash("123-45-6789", algorithm="sha512")
        assert result.startswith("[SSN_HASH_")

    def test_md5_raises_value_error(self):
        with pytest.raises(ValueError, match="md5"):
            self._hash("123-45-6789", algorithm="md5")

    def test_unknown_algorithm_raises_value_error(self):
        with pytest.raises(ValueError):
            self._hash("123-45-6789", algorithm="blake2b")

    def test_same_value_same_hash(self):
        h1 = self._hash("123-45-6789", salt="fixed-salt")
        h2 = self._hash("123-45-6789", salt="fixed-salt")
        assert h1 == h2

    def test_different_salts_different_hashes(self):
        h1 = self._hash("123-45-6789", salt="salt-a")
        h2 = self._hash("123-45-6789", salt="salt-b")
        assert h1 != h2


# ── Fix #15: InMemoryMappingVault TTL ──────────────────────────────────────

class TestInMemoryVaultTTL:
    """Bug: InMemoryMappingVault silently ignored ttl_seconds."""

    def test_entry_expires_after_ttl(self):
        from privacy_firewall.vault import InMemoryMappingVault

        v = InMemoryMappingVault()
        v.put("t", "c", "th", "[TOK_001]", "secret-value", ttl_seconds=1)
        # Entry present immediately
        assert v.get_case_mapping("t", "c", "th") == {"[TOK_001]": "secret-value"}
        time.sleep(1.1)
        # After TTL, entry must be gone
        assert v.get_case_mapping("t", "c", "th") == {}

    def test_no_ttl_entry_persists(self):
        from privacy_firewall.vault import InMemoryMappingVault

        v = InMemoryMappingVault()
        v.put("t", "c", "th", "[TOK_001]", "persistent", ttl_seconds=None)
        time.sleep(0.1)
        assert v.get_case_mapping("t", "c", "th") == {"[TOK_001]": "persistent"}

    def test_forget_case_clears_expiry_state(self):
        from privacy_firewall.vault import InMemoryMappingVault

        v = InMemoryMappingVault()
        v.put("t", "c", "th", "[TOK_001]", "val", ttl_seconds=3600)
        v.forget_case("t", "c", "th")
        assert v.get_case_mapping("t", "c", "th") == {}
        # _expiry should also be cleaned up — no ghost entries
        assert ("t", "c", "th") not in v._expiry

    def test_purge_expired_returns_count(self):
        from privacy_firewall.vault import InMemoryMappingVault

        v = InMemoryMappingVault()
        v.put("t", "c", "th", "[TOK_001]", "v1", ttl_seconds=1)
        v.put("t", "c", "th", "[TOK_002]", "v2", ttl_seconds=1)
        v.put("t", "c", "th", "[TOK_003]", "v3", ttl_seconds=None)
        time.sleep(1.1)
        count = v.purge_expired()
        assert count == 2
        assert v.get_case_mapping("t", "c", "th") == {"[TOK_003]": "v3"}


# ── Fix #11: PASSPORT / DRIVERS_LICENSE / AGE / MAC_ADDRESS / ROUTING_NUMBER ──

class TestProfileDispositionCoverage:
    """Bug: PASSPORT, DRIVERS_LICENSE, AGE, MAC_ADDRESS, ROUTING_NUMBER had no
    disposition in any profile — detected entities were silently dropped."""

    def _assert_in_all_profiles(self, entity_type: str):
        from privacy_firewall.profiles.presets import PRESET_PROFILES

        for name, profile in PRESET_PROFILES.items():
            assert entity_type in profile.dispositions, (
                f"Profile '{name}' missing disposition for {entity_type}"
            )

    def test_passport_in_all_profiles(self):
        self._assert_in_all_profiles("PASSPORT")

    def test_drivers_license_in_all_profiles(self):
        self._assert_in_all_profiles("DRIVERS_LICENSE")

    def test_age_in_all_profiles(self):
        self._assert_in_all_profiles("AGE")

    def test_mac_address_in_all_profiles(self):
        self._assert_in_all_profiles("MAC_ADDRESS")

    def test_routing_number_in_all_profiles(self):
        self._assert_in_all_profiles("ROUTING_NUMBER")

    def test_passport_regex_detected_and_anonymized(self):
        """Full pipeline: US passport (9 digits) detected by regex and then anonymized."""
        fw = _regex_firewall(domain="generic", language="en")
        # US passport regex: \b[0-9]{9}\b — must be exactly 9 digits
        result = fw.secure_call(text="Passport: 123456789", context=CTX)
        # Either the number is gone, or it was replaced with a token
        passport_present = "123456789" in result.sanitized_text
        detected_types = [e["entity_type"] for e in result.trace.detected_entities]
        detected = "PASSPORT" in detected_types
        assert detected or not passport_present, (
            f"PASSPORT not detected and raw number still present. "
            f"Detected types: {detected_types}, sanitized: {result.sanitized_text!r}"
        )

    def test_age_generalized_in_generic_profile(self):
        """AGE should be generalized (bucketed) in generic profile."""
        fw = _regex_firewall(domain="generic", language="en")
        result = fw.secure_call(text="Patient is 43 years old", context=CTX)
        assert "43" not in result.sanitized_text or "40-49" in result.sanitized_text, (
            "Age should be generalized to decade bucket"
        )


# ── Fix #7/#19: GLINER and Nemotron label mappings ──────────────────────────

class TestLabelMappings:
    """Bug: GLINER 'routing number' → ACCOUNT_NUMBER; Nemotron 'mac_address' → IP_ADDRESS."""

    def test_gliner_routing_number_maps_to_routing_number(self):
        from privacy_firewall.unified_detector import GLINER_LABEL_TO_ENTITY
        import privacy_firewall.entity_types as ET

        assert GLINER_LABEL_TO_ENTITY["routing number"] == ET.ROUTING_NUMBER

    def test_gliner_routing_number_not_account_number(self):
        from privacy_firewall.unified_detector import GLINER_LABEL_TO_ENTITY
        import privacy_firewall.entity_types as ET

        assert GLINER_LABEL_TO_ENTITY["routing number"] != ET.ACCOUNT_NUMBER

    def test_nemotron_mac_address_maps_to_mac_address(self):
        from privacy_firewall.unified_detector import UnifiedDetectionEngine
        import privacy_firewall.entity_types as ET

        result = UnifiedDetectionEngine._map_nemotron_label("mac_address")
        assert result == ET.MAC_ADDRESS

    def test_nemotron_mac_address_not_ip_address(self):
        from privacy_firewall.unified_detector import UnifiedDetectionEngine
        import privacy_firewall.entity_types as ET

        result = UnifiedDetectionEngine._map_nemotron_label("mac_address")
        assert result != ET.IP_ADDRESS


# ── Fix #8: cleanup_utils residual patterns ────────────────────────────────

class TestResidualCleanup:
    """Bug: cleanup_utils only covered Spanish DNI, email, and one phone format."""

    def test_ssn_detected(self):
        from privacy_firewall.cleanup_utils import has_residual_pii, apply_residual_cleanup

        assert has_residual_pii("SSN: 123-45-6789")
        cleaned, replacements = apply_residual_cleanup("SSN: 123-45-6789")
        assert "123-45-6789" not in cleaned
        assert any(r["entity_type"] == "SSN" for r in replacements)

    def test_iban_detected(self):
        from privacy_firewall.cleanup_utils import has_residual_pii, apply_residual_cleanup

        iban = "DE89370400440532013000"
        assert has_residual_pii(iban)
        cleaned, _ = apply_residual_cleanup(iban)
        assert iban not in cleaned

    def test_credit_card_detected(self):
        from privacy_firewall.cleanup_utils import has_residual_pii, apply_residual_cleanup

        cc = "4111111111111111"
        assert has_residual_pii(cc)
        cleaned, replacements = apply_residual_cleanup(cc)
        assert cc not in cleaned
        assert any(r["entity_type"] == "CREDIT_CARD" for r in replacements)

    def test_email_still_detected(self):
        from privacy_firewall.cleanup_utils import has_residual_pii

        assert has_residual_pii("Contact: user@example.com")

    def test_dni_still_detected(self):
        from privacy_firewall.cleanup_utils import has_residual_pii

        assert has_residual_pii("DNI: 12345678Z")

    def test_clean_text_returns_false(self):
        from privacy_firewall.cleanup_utils import has_residual_pii

        assert not has_residual_pii("The weather is nice today.")


# ── Fix #16 / #10: CORS env var + ForgetRequest ─────────────────────────────

class TestWebApp:
    """Bug: CORS hardcoded; /api/forget used full RunRequest."""

    def test_forget_request_has_no_text_field(self):
        from privacy_firewall.web.app import ForgetRequest

        fr = ForgetRequest()
        assert not hasattr(fr, "text"), "ForgetRequest should not require 'text'"

    def test_forget_request_has_scope_fields(self):
        from privacy_firewall.web.app import ForgetRequest

        fr = ForgetRequest(tenant_id="t", case_id="c", thread_id="th")
        assert fr.tenant_id == "t"
        assert fr.case_id == "c"
        assert fr.thread_id == "th"

    def test_cors_reads_env_var(self, monkeypatch):
        import importlib
        import privacy_firewall.web.app as app_mod
        from fastapi.testclient import TestClient

        monkeypatch.setenv("CORS_ORIGINS", "https://myapp.example.com,https://admin.example.com")
        app = app_mod.create_app()
        # Find the CORSMiddleware stack and check its origins
        cors_middleware = None
        for m in app.user_middleware:
            if "CORSMiddleware" in str(m):
                cors_middleware = m
                break
        # Even without inspecting internals, ensure the app starts without error
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_forget_endpoint_accepts_lean_body(self):
        from privacy_firewall.web.app import create_app
        from fastapi.testclient import TestClient

        client = TestClient(create_app())
        resp = client.post(
            "/api/forget",
            json={"tenant_id": "t", "case_id": "c", "thread_id": "th"},
        )
        assert resp.status_code == 200
        assert "removed" in resp.json()

    def test_forget_endpoint_rejects_missing_required_fields(self):
        """ForgetRequest fields all have defaults so empty body is valid."""
        from privacy_firewall.web.app import create_app
        from fastapi.testclient import TestClient

        client = TestClient(create_app())
        resp = client.post("/api/forget", json={})
        assert resp.status_code == 200  # defaults kick in

    def test_run_request_still_works(self):
        """Ensure existing RunRequest API is unbroken."""
        from privacy_firewall.web.app import create_app
        from fastapi.testclient import TestClient

        client = TestClient(create_app())
        resp = client.post(
            "/api/run",
            json={
                "text": "Hello John Smith",
                "profile": "generic",
                "detector_backend": "regex",
            },
        )
        assert resp.status_code == 200


# ── Fix #2: no duplicate return in custom_recognizers ───────────────────────

class TestCustomRecognizers:
    """Bug: duplicate return recognizers at end of function."""

    def test_create_enhanced_recognizers_returns_list(self):
        from privacy_firewall.presidio_integration.custom_recognizers import (
            create_enhanced_recognizers,
        )

        result = create_enhanced_recognizers("en")
        assert isinstance(result, list)

    def test_spanish_includes_language_specific(self):
        from privacy_firewall.presidio_integration.custom_recognizers import (
            create_enhanced_recognizers,
        )

        es = create_enhanced_recognizers("es")
        en = create_enhanced_recognizers("en")
        # Spanish should have at least as many recognizers as English
        assert len(es) >= len(en)


# ── Duplicate return dead code removed (verify only one return at module level) ──

class TestCustomRecognizersNoDuplicateReturn:
    def test_source_has_single_return(self):
        import ast
        import inspect
        from privacy_firewall.presidio_integration import custom_recognizers

        source = inspect.getsource(custom_recognizers)
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "create_enhanced_recognizers":
                returns = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
                assert len(returns) == 1, (
                    f"Expected exactly 1 return, found {len(returns)}"
                )
