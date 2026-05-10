"""Language routing system for NLP engine and pattern selection.

Routes detected language to appropriate:
- Presidio NlpEngine (spaCy or transformers)
- Locale-specific regex patterns
- Domain recognizers
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Any, Protocol


class NLPEngineProtocol(Protocol):
    """Protocol for NLP engines (spaCy, transformers, etc.)."""
    
    def analyze(self, text: str) -> Any:
        """Analyze text and return NLP structures."""
        ...


@dataclass
class LanguageConfig:
    """Configuration for a specific language."""
    
    language_code: str  # ISO 639-1 code (e.g., 'es', 'en')
    spacy_model: str | None = None  # spaCy model name (e.g., 'es_core_news_sm')
    transformer_model: str | None = None  # HuggingFace model (e.g., 'dslim/bert-base-NER')
    patterns_locale: str | None = None  # Locale for pattern catalog (e.g., 'ES', 'US')
    supports_pos_tagging: bool = True  # Whether model has POS tagging
    supports_ner: bool = True  # Whether model has NER
    
    def __post_init__(self) -> None:
        # Default patterns_locale to uppercase language code
        if self.patterns_locale is None:
            self.patterns_locale = self.language_code.upper()


# Language configuration catalog
# This maps language codes to their optimal NLP configuration
DEFAULT_LANGUAGE_CONFIGS: dict[str, LanguageConfig] = {
    "es": LanguageConfig(
        language_code="es",
        spacy_model="es_core_news_sm",
        transformer_model="PlanTL-GOB-ES/roberta-base-bne",
        patterns_locale="ES",
    ),
    "en": LanguageConfig(
        language_code="en",
        spacy_model="en_core_web_sm",
        transformer_model="dslim/bert-base-NER",
        patterns_locale="US",
    ),
    "fr": LanguageConfig(
        language_code="fr",
        spacy_model="fr_core_news_sm",
        transformer_model="Jean-Baptiste/camembert-ner",
        patterns_locale="FR",
    ),
    "de": LanguageConfig(
        language_code="de",
        spacy_model="de_core_news_sm",
        transformer_model="dbmdz/bert-large-cased-finetuned-conll03-english",
        patterns_locale="DE",
    ),
    "it": LanguageConfig(
        language_code="it",
        spacy_model="it_core_news_sm",
        transformer_model="dbmdz/bert-base-italian-cased",
        patterns_locale="IT",
    ),
    "pt": LanguageConfig(
        language_code="pt",
        spacy_model="pt_core_news_sm",
        transformer_model="neuralmind/bert-base-portuguese-cased",
        patterns_locale="PT",
    ),
    "nl": LanguageConfig(
        language_code="nl",
        spacy_model="nl_core_news_sm",
        transformer_model="wietsedv/bert-base-dutch-cased",
        patterns_locale="NL",
    ),
    "ca": LanguageConfig(
        language_code="ca",
        spacy_model="ca_core_news_sm",
        patterns_locale="ES",  # Use Spanish patterns as fallback
    ),
    # Multilingual fallback
    "xx": LanguageConfig(
        language_code="xx",
        spacy_model="xx_ent_wiki_sm",
        transformer_model="xlm-roberta-base",
        patterns_locale="GLOBAL",
        supports_pos_tagging=False,  # Multilingual model has limited POS
    ),
}


@dataclass
class LanguageRouter:
    """Routes language to appropriate NLP engine and pattern catalog.
    
    Handles:
    - Auto-download of missing models
    - Fallback to multilingual model if language-specific unavailable
    - Lazy loading (models loaded on first use)
    - Caching of loaded engines
    """
    
    language_configs: dict[str, LanguageConfig] = field(default_factory=lambda: DEFAULT_LANGUAGE_CONFIGS.copy())
    backend: str = "spacy"  # "spacy" or "transformers"
    auto_download: bool = field(
        default_factory=lambda: os.getenv("PII_FIREWALL_AUTO_DOWNLOAD_MODELS", "0") in ("1", "true", "True")
    )
    
    # Cached engines
    _loaded_engines: dict[str, Any] = field(default_factory=dict, init=False, repr=False)
    
    def get_config(self, language: str) -> LanguageConfig:
        """Get language configuration, with fallback to multilingual."""
        if language in self.language_configs:
            return self.language_configs[language]
        
        # Fallback to multilingual
        print(f"⚠ Language '{language}' not configured. Falling back to multilingual model.")
        return self.language_configs["xx"]
    
    def get_engine(self, language: str):
        """Get or load NLP engine for language.
        
        Returns cached engine if already loaded, otherwise loads and caches.
        """
        if language in self._loaded_engines:
            return self._loaded_engines[language]
        
        config = self.get_config(language)
        
        if self.backend == "spacy":
            engine = self._load_spacy_engine(config)
        elif self.backend == "transformers":
            engine = self._load_transformer_engine(config)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")
        
        self._loaded_engines[language] = engine
        return engine
    
    def _load_spacy_engine(self, config: LanguageConfig):
        """Load spaCy NLP engine for language."""
        import spacy
        import subprocess
        import sys
        
        model_name = config.spacy_model
        if not model_name:
            raise ValueError(f"No spaCy model configured for language {config.language_code}")
        
        try:
            nlp = spacy.load(model_name)
            print(f"[OK] Loaded spaCy model: {model_name}")
            return nlp
        except OSError:
            if not self.auto_download:
                raise RuntimeError(
                    f"spaCy model '{model_name}' not found. "
                    f"Install with: python -m spacy download {model_name}"
                )
            
            # Auto-download
            print(f"⚠ Model {model_name} not found. Downloading...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "spacy", "download", model_name],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                nlp = spacy.load(model_name)
                print(f"✓ Successfully downloaded and loaded: {model_name}")
                return nlp
            except (subprocess.CalledProcessError, OSError) as e:
                print(f"✗ Failed to download {model_name}: {e}")
                print(f"  Falling back to multilingual model")
                
                # Try multilingual fallback
                fallback = self.language_configs["xx"]
                return self._load_spacy_engine(fallback)
    
    def _load_transformer_engine(self, config: LanguageConfig):
        """Load HuggingFace transformers NLP engine for language.
        
        This is a placeholder for transformer-based NER.
        Full implementation would use transformers.pipeline with custom NER.
        """
        model_name = config.transformer_model
        if not model_name:
            raise ValueError(f"No transformer model configured for language {config.language_code}")
        
        try:
            from transformers import pipeline  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "transformers is not installed. "
                "Install with: pip install 'pii-firewall[transformers]'"
            ) from exc
        
        # Load NER pipeline
        # Note: This downloads the model automatically from HuggingFace Hub
        print(f"Loading transformer model: {model_name}...")
        nlp = pipeline("ner", model=model_name, aggregation_strategy="simple")
        print(f"✓ Loaded transformer model: {model_name}")
        
        return nlp
    
    def get_patterns_locale(self, language: str) -> str:
        """Get locale code for pattern catalog lookup."""
        config = self.get_config(language)
        return config.patterns_locale or "GLOBAL"
    
    def supports_pos_tagging(self, language: str) -> bool:
        """Check if language model supports POS tagging."""
        config = self.get_config(language)
        return config.supports_pos_tagging
    
    def add_language(self, language_code: str, config: LanguageConfig) -> None:
        """Add or override language configuration."""
        self.language_configs[language_code] = config
    
    def preload_languages(self, languages: list[str]) -> None:
        """Preload NLP engines for multiple languages.
        
        Useful for:
        - Warming up on server startup
        - Avoiding first-request latency
        - Testing all models are available
        """
        for lang in languages:
            try:
                self.get_engine(lang)
            except Exception as e:
                print(f"✗ Failed to preload {lang}: {e}")
