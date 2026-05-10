from __future__ import annotations

from privacy_firewall import (
    PrivacyFirewallSDK,
    create_custom_profile,
    get_preset_profile,
)


TEST_CONTEXT = {
    "tenant_id": "test-tenant",
    "case_id": "test-case",
    "thread_id": "test-thread",
    "actor_id": "test-user",
}


def _build_sdk_with_email_pseudonymization() -> PrivacyFirewallSDK:
    profile = create_custom_profile(
        name="test-secure-call",
        base_profile=get_preset_profile("generic"),
        linguistic_filter_enabled=False,
    )

    sdk = PrivacyFirewallSDK.create(
        profile=profile,
        language="en",
        detector_backend="regex",
    )
    # Force deterministic reversible behavior for EMAIL in this test.
    sdk.firewall.add_custom_regex(
        entity_type="TEST_EMAIL",
        regex=r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b",
        disposition_action="pseudonymize",
        confidence_threshold=0.0,
    )
    return sdk


def test_secure_call_roundtrip_with_callable_prompt_only() -> None:
    sdk = _build_sdk_with_email_pseudonymization()

    def llm_client(prompt: str) -> str:
        # Returns anonymized prompt as a model would do in a no-op transform.
        return prompt

    result = sdk.secure_call(
        text="Contact Ana at ana@example.com",
        context=TEST_CONTEXT,
        llm_client=llm_client,
    )

    assert "ana@example.com" not in result.sanitized_text
    assert "ana@example.com" in result.final_text


def test_secure_call_roundtrip_with_generate_method() -> None:
    sdk = _build_sdk_with_email_pseudonymization()

    class EchoModel:
        def generate(self, prompt: str, context_capsule: dict) -> str:
            assert context_capsule["tenant_id"] == "test-tenant"
            return f"Model saw: {prompt}"

    result = sdk.secure_call(
        text="Send report to ana@example.com",
        context=TEST_CONTEXT,
        llm_client=EchoModel(),
    )

    assert "ana@example.com" not in result.sanitized_text
    assert "ana@example.com" in result.final_text
    assert "Model saw:" in result.model_output


def test_secure_call_stream_roundtrip_with_chunked_callable() -> None:
    sdk = _build_sdk_with_email_pseudonymization()

    def streaming_like_client(prompt: str):
        # Return very small chunks to force token splits across boundaries.
        for i in range(0, len(prompt), 2):
            yield prompt[i : i + 2]

    chunks = list(
        sdk.secure_call_stream(
            text="Email is ana@example.com",
            context=TEST_CONTEXT,
            llm_client=streaming_like_client,
        )
    )
    assert len(chunks) > 1
    final_text = "".join(chunks)

    assert "ana@example.com" in final_text
    assert "TEST_EMAIL_1" not in final_text


def test_secure_call_stream_roundtrip_with_generate_stream_method() -> None:
    sdk = _build_sdk_with_email_pseudonymization()

    class StreamingEchoModel:
        def generate_stream(self, prompt: str, context_capsule: dict):
            assert context_capsule["thread_id"] == "test-thread"
            yield "ChunkA: "
            for i in range(0, len(prompt), 3):
                yield prompt[i : i + 3]

    chunks = list(
        sdk.secure_call_stream(
            text="Contact ana@example.com now",
            context=TEST_CONTEXT,
            llm_client=StreamingEchoModel(),
        )
    )
    assert len(chunks) > 1
    final_text = "".join(chunks)

    assert final_text.startswith("ChunkA: ")
    assert "ana@example.com" in final_text


def test_secure_call_stream_falls_back_to_non_stream_callable() -> None:
    sdk = _build_sdk_with_email_pseudonymization()

    def non_stream_client(prompt: str) -> str:
        return f"Single response: {prompt}"

    chunks = list(
        sdk.secure_call_stream(
            text="Contact ana@example.com",
            context=TEST_CONTEXT,
            llm_client=non_stream_client,
        )
    )
    final_text = "".join(chunks)

    assert final_text.startswith("Single response:")
    assert "ana@example.com" in final_text


def test_secure_call_backward_compat_with_streaming_callable_in_non_stream_api() -> None:
    sdk = _build_sdk_with_email_pseudonymization()

    def streaming_like_client(prompt: str):
        yield prompt

    result = sdk.secure_call(
        text="Email is ana@example.com",
        context=TEST_CONTEXT,
        llm_client=streaming_like_client,
    )

    # Non-stream secure_call intentionally keeps backward behavior.
    assert "generator object" in result.model_output


def test_secure_call_openai_style_sync_client() -> None:
    sdk = _build_sdk_with_email_pseudonymization()

    class OpenAIStyleClient:
        """Provider-style adapter with generate(prompt, context_capsule)."""

        def generate(self, prompt: str, context_capsule: dict) -> str:
            assert context_capsule["thread_id"] == "test-thread"
            return f"OpenAI answer: {prompt}"

    result = sdk.secure_call(
        text="Reach ana@example.com for follow-up",
        context=TEST_CONTEXT,
        llm_client=OpenAIStyleClient(),
    )

    assert result.model_output.startswith("OpenAI answer:")
    assert "ana@example.com" in result.final_text


def test_secure_call_stream_openai_style_stream_client() -> None:
    sdk = _build_sdk_with_email_pseudonymization()

    class OpenAIStyleStreamingClient:
        """Provider-style adapter with generate_stream(prompt, context_capsule)."""

        def generate_stream(self, prompt: str, context_capsule: dict):
            assert context_capsule["tenant_id"] == "test-tenant"
            payload = f"OpenAI stream: {prompt}"
            for i in range(0, len(payload), 4):
                yield payload[i : i + 4]

    chunks = list(
        sdk.secure_call_stream(
            text="Reach ana@example.com for follow-up",
            context=TEST_CONTEXT,
            llm_client=OpenAIStyleStreamingClient(),
        )
    )

    assert len(chunks) > 1
    final_text = "".join(chunks)
    assert final_text.startswith("OpenAI stream:")
    assert "ana@example.com" in final_text


def test_secure_call_provider_style_sync_callable() -> None:
    sdk = _build_sdk_with_email_pseudonymization()

    def provider_like_callable(prompt: str, context_capsule: dict) -> str:
        assert context_capsule["case_id"] == "test-case"
        return f"Provider answer: {prompt}"

    result = sdk.secure_call(
        text="Patient email ana@example.com requires review",
        context=TEST_CONTEXT,
        llm_client=provider_like_callable,
    )

    assert result.model_output.startswith("Provider answer:")
    assert "ana@example.com" in result.final_text


def test_secure_call_stream_provider_style_stream_callable() -> None:
    sdk = _build_sdk_with_email_pseudonymization()

    def provider_like_stream_callable(prompt: str, context_capsule: dict):
        assert context_capsule["thread_id"] == "test-thread"
        payload = f"Provider stream: {prompt}"
        for i in range(0, len(payload), 5):
            yield payload[i : i + 5]

    chunks = list(
        sdk.secure_call_stream(
            text="Patient email ana@example.com requires review",
            context=TEST_CONTEXT,
            llm_client=provider_like_stream_callable,
        )
    )

    assert len(chunks) > 1
    final_text = "".join(chunks)
    assert final_text.startswith("Provider stream:")
    assert "ana@example.com" in final_text
