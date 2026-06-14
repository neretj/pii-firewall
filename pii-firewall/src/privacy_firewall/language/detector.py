"""Fast language detection with thread-level caching.

Two strategies:
1. Thread-level detection: Detect once per thread, cache for all messages
2. Message-level detection: Detect on each message (mixed-language threads)

Recommendation: Thread-level is preferred for 99% of use cases. It's faster,
reduces latency, and most conversations are single-language. Message-level
should only be enabled for explicit multilingual scenarios.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
import logging
import time

_logger = logging.getLogger(__name__)


class LanguageDetectorProtocol(Protocol):
    """Protocol for language detection implementations."""
    
    def detect(self, text: str) -> str:
        """Detect language from text. Returns ISO 639-1 code (e.g., 'es', 'en')."""
        ...


@dataclass
class ThreadLanguageCache:
    """Cache for thread-level language detection.
    
    Stores detected language per thread_id to avoid re-detection on every message.
    Includes TTL to handle language switches within long-running threads.
    """
    
    ttl_seconds: int = 3600  # 1 hour default
    _cache: dict[str, tuple[str, float]] = field(default_factory=dict, init=False, repr=False)
    
    def get(self, thread_id: str) -> str | None:
        """Get cached language for thread, or None if not cached/expired."""
        if thread_id not in self._cache:
            return None
        
        lang, timestamp = self._cache[thread_id]
        if time.time() - timestamp > self.ttl_seconds:
            del self._cache[thread_id]
            return None
        
        return lang
    
    def set(self, thread_id: str, language: str) -> None:
        """Cache detected language for thread."""
        self._cache[thread_id] = (language, time.time())
    
    def clear(self, thread_id: str) -> None:
        """Clear cached language for thread (e.g., on explicit language switch)."""
        self._cache.pop(thread_id, None)
    
    def purge_expired(self) -> int:
        """Remove expired entries. Returns count of purged entries."""
        now = time.time()
        expired = [
            tid for tid, (_, ts) in self._cache.items()
            if now - ts > self.ttl_seconds
        ]
        for tid in expired:
            del self._cache[tid]
        return len(expired)


@dataclass
class LanguageDetector:
    """Fast language detector using langdetect (Google's language detection).
    
    langdetect is chosen for:
    - Speed: ~1-2ms per detection vs ~50ms for spaCy
    - Accuracy: 99.8% on sentences >20 chars
    - No model download required
    - Supports 55 languages
    
    Alternative backends can be swapped via LanguageDetectorProtocol.
    """
    
    fallback_language: str = "en"
    min_text_length: int = 10  # Require at least N chars for reliable detection
    
    def __post_init__(self) -> None:
        try:
            from langdetect import detect, LangDetectException  # type: ignore
            self._detect = detect
            self._exception = LangDetectException
        except ImportError as exc:
            raise ImportError(
                "langdetect is not installed. "
                "Install with: pip install 'pii-firewall[langdetect]' or pip install langdetect"
            ) from exc
    
    def detect(self, text: str) -> str:
        """Detect language from text. Returns ISO 639-1 code."""
        lang, _ = self.detect_with_confidence(text)
        return lang

    def detect_with_confidence(self, text: str) -> tuple[str, float]:
        """Detect language and return (lang_code, probability 0-1).

        Returns (fallback_language, 0.0) on short, ambiguous, or failed input.
        """
        if not text or len(text.strip()) < self.min_text_length:
            return self.fallback_language, 0.0

        try:
            candidates = self._detect_langs(text)
            if not candidates:
                return self.fallback_language, 0.0
            top = candidates[0]
            return top.lang, getattr(top, "prob", 0.0)
        except self._exception:
            return self.fallback_language, 0.0
        except Exception:
            return self.fallback_language, 0.0


@dataclass
class FastTextLanguageDetector:
    """Alternative detector using FastText (Facebook's language identification).
    
    Pros:
    - Faster than langdetect (~0.5ms)
    - Supports 176 languages
    - Better on short texts
    
    Cons:
    - Requires downloading a 126MB model
    - Less accurate on very short texts
    
    Usage:
        detector = FastTextLanguageDetector()
        lang = detector.detect("Hola mundo")  # Returns 'es'
    """
    
    fallback_language: str = "en"
    model_path: str | None = None  # Path to .bin model, or None to auto-download
    
    def __post_init__(self) -> None:
        try:
            import fasttext  # type: ignore
            import urllib.request
            from pathlib import Path
            
            self._fasttext = fasttext
            
            # Auto-download model if not provided
            if self.model_path is None:
                model_dir = Path.home() / ".pii-firewall" / "models"
                model_dir.mkdir(parents=True, exist_ok=True)
                self.model_path = str(model_dir / "lid.176.bin")
                
                if not Path(self.model_path).exists():
                    _logger.info("Downloading FastText language model to %s...", self.model_path)
                    url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
                    urllib.request.urlretrieve(url, self.model_path)
                    _logger.info("FastText language model downloaded.")
            
            # Load model (suppresses FastText warnings)
            self._model = fasttext.load_model(self.model_path)
            
        except ImportError as exc:
            raise ImportError(
                "fasttext is not installed. "
                "Install with: pip install fasttext"
            ) from exc
    
    def detect(self, text: str) -> str:
        """Detect language from text. Returns ISO 639-1 code."""
        if not text or len(text.strip()) < 5:
            return self.fallback_language
        
        try:
            # FastText returns format: (('__label__en',), array([0.99]))
            predictions = self._model.predict(text.replace("\n", " "), k=1)
            label = predictions[0][0]  # e.g., '__label__en'
            lang_code = label.replace("__label__", "")
            
            # Map FastText codes to ISO 639-1 if needed
            # FastText uses ISO 639-1 already for most languages
            return lang_code
            
        except Exception:
            return self.fallback_language


def create_language_detector(backend: str = "langdetect", **kwargs) -> LanguageDetectorProtocol:
    """Factory function to create language detector.
    
    Args:
        backend: "langdetect" (default, fast, accurate) or "fasttext" (faster, more languages)
        **kwargs: Additional arguments passed to detector constructor
    
    Returns:
        LanguageDetectorProtocol implementation
    """
    if backend == "langdetect":
        return LanguageDetector(**kwargs)
    elif backend == "fasttext":
        return FastTextLanguageDetector(**kwargs)
    else:
        raise ValueError(f"Unknown language detector backend: {backend}. Choose 'langdetect' or 'fasttext'")
