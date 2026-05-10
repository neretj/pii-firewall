from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, Iterator
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMClientProtocol(Protocol):
    """Protocol for model clients used by secure_call.

    Implementations should accept anonymized prompt text plus minimal context.
    """

    def generate(self, prompt: str, context_capsule: dict) -> str:
        ...


@dataclass
class MockLLMClient:
    """Simple deterministic test client.

    This class intentionally avoids vendor SDK dependencies and is only meant
    for tests/examples.
    """

    prefix: str = "[MOCK_LLM]"

    def generate(self, prompt: str, context_capsule: dict) -> str:
        return f"{self.prefix} {prompt}"


def call_model(model: Any, prompt: str, context_capsule: dict) -> str:
    """Invoke any model adapter.

    Supported forms:
    - Object implementing .generate(prompt, context_capsule)
    - Callable(prompt, context_capsule)
    - Callable(prompt)
    """

    if model is None:
        return prompt

    generate = getattr(model, "generate", None)
    if callable(generate):
        return str(generate(prompt, context_capsule))

    if callable(model):
        try:
            return str(model(prompt, context_capsule))
        except TypeError:
            return str(model(prompt))

    raise TypeError(
        "Unsupported model adapter. Provide an object with generate(prompt, context_capsule) "
        "or a callable(prompt, context_capsule)."
    )


def _is_stream_like(value: Any) -> bool:
    if isinstance(value, (str, bytes, bytearray)):
        return False
    return isinstance(value, Iterable)


def _to_str_stream(value: Any) -> Iterator[str]:
    if _is_stream_like(value):
        for chunk in value:
            yield str(chunk)
        return
    yield str(value)


def stream_model(model: Any, prompt: str, context_capsule: dict) -> Iterator[str]:
    """Stream model output chunks.

    Supported forms:
    - Object implementing .generate_stream(prompt, context_capsule)
    - Object implementing .generate(prompt, context_capsule) returning string or iterable
    - Callable(prompt, context_capsule) returning string or iterable
    - Callable(prompt) returning string or iterable
    """

    if model is None:
        yield prompt
        return

    generate_stream = getattr(model, "generate_stream", None)
    if callable(generate_stream):
        yield from _to_str_stream(generate_stream(prompt, context_capsule))
        return

    generate = getattr(model, "generate", None)
    if callable(generate):
        yield from _to_str_stream(generate(prompt, context_capsule))
        return

    if callable(model):
        try:
            result = model(prompt, context_capsule)
        except TypeError:
            result = model(prompt)
        yield from _to_str_stream(result)
        return

    raise TypeError(
        "Unsupported model adapter. Provide an object with generate_stream(prompt, context_capsule), "
        "generate(prompt, context_capsule), or a callable(prompt, context_capsule)."
    )