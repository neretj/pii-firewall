# PII Firewall 🛡️

**Open-source PII firewall for LLM apps — detect, anonymize and rehydrate sensitive data before it reaches OpenAI, Anthropic or any LLM provider**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![PyPI](https://img.shields.io/pypi/v/pii-firewall.svg)](https://pypi.org/project/pii-firewall/)

## Why PII Firewall?

Most PII tools were built for data pipelines, not for LLM calls. PII Firewall is designed specifically around the **detect → sanitize → LLM → rehydrate** round-trip:

- **Domain awareness** — keep relevant data (medical diagnoses in healthcare, transaction amounts in finance) so the LLM still has context, while stripping what must not leave your system
- **Auto language detection** — 55+ languages detected automatically with thread-level caching (0 ms after the first call)
- **Locale-specific patterns** — country-specific ID formats: Spanish DNI, US SSN, French INSEE, German Steuernummer, Italian Codice Fiscale, Portuguese NIF, and more
- **7 detection backends** — regex, Presidio, Hybrid, GLiNER, Transformers, OPF, Nemotron — switch with one parameter
- **7 disposition actions** — Keep, Redact, Pseudonymize, Generalize, Mask, Hash, Suppress
- **Reversible pseudonymization** — vault stores original↔token mappings; real names are restored in LLM responses
- **Streaming support** — `secure_call_stream()` yields rehydrated tokens in real-time
- **GDPR Art. 17 right to forget** — `firewall.forget()` wipes all mappings for a thread or case

## 📦 Quick Start

### Installation

```bash
# From PyPI (basic, pattern-based)
pip install pii-firewall

# Recommended: With Presidio and language detection
pip install "pii-firewall[presidio,langdetect]"

# Full features (includes transformers, OPF, GLiNER)
pip install "pii-firewall[all]"

# Local development install
pip install -e .

# Focused installs
pip install "pii-firewall[opf]"       # OPF runtime (or install from source if your environment requires it)
pip install "pii-firewall[gliner]"    # GLiNER PII models
```

### Basic Usage

```python
from privacy_firewall import create_firewall

# Create healthcare firewall (auto-detects language)
firewall = create_firewall("healthcare")

# Process text
result = firewall.process(
    text="Ana García, 43 años, hipertensión. Prescripción: enalapril 10mg.",
    context={
        "tenant_id": "hospital-001",
        "case_id": "patient-123",
        "thread_id": "consultation-1",
        "actor_id": "doctor-456",
    },
)

print(result.sanitized_text)
# Output: "PERSON_1, [AGE_40-49], hipertensión. enalapril 10mg."
# Notice: Medical terms (hipertensión, enalapril) are KEPT!
```

## 🎯 Domain Profiles

### Healthcare
Keeps medical data relevant for diagnosis while protecting patient identity:
```python
firewall = create_firewall("healthcare")

# Keeps: diagnoses, medications, procedures, lab values
# Redacts: names, IDs, addresses
# Generalizes: ages (43 → 40-49), dates (specific → month/year)
```

### Finance
Protects customer PII and financial identifiers. Amounts and transaction context pass through without detection (not regulated PII):
```python
firewall = create_firewall("finance")

# Keeps: company names, transaction context (amounts pass through as non-PII)
# Masks: credit card numbers (4111...1111)
# Pseudonymizes: account numbers, IBANs, tax IDs (reversible)
# Redacts: customer PII (names, addresses) and medical data
```

### Legal
High anonymity for legal documents:
```python
firewall = create_firewall("legal")

# Keeps: company/firm names (courts, agencies — public record)
# Note: statutes, case numbers, legal citations are public record and pass through
# Pseudonymizes: party names (reversible for case management)
# Generalizes: all dates to month/year
# Redacts: strong identifiers and cross-domain medical data
```

## 🌍 Multi-Language Support

Auto-detects 55+ languages with 0ms overhead after first detection:

```python
firewall = create_firewall("healthcare")

# Spanish - detected automatically
result_es = firewall.process(
    text="Paciente con diabetes tipo 2, DNI 12345678A",
    context={...}
)

# English - detected automatically  
result_en = firewall.process(
    text="Patient with type 2 diabetes, SSN 123-45-6789",
    context={...}
)

# French - detected automatically
result_fr = firewall.process(
    text="Patient avec diabète, INSEE 1234567890123",
    context={...}
)
```

**Supported locales**: ES, US, FR, DE, IT, PT, + global patterns

## 🔧 Advanced Usage

### Custom Profiles

```python
from privacy_firewall import (
    PrivacyFirewall,
    create_custom_profile,
    EntityDisposition,
    DispositionAction,
)

# Create custom profile
profile = create_custom_profile("legal_discovery")

# Add entity dispositions
profile.add_disposition(EntityDisposition(
    entity_type="PERSON",
    action=DispositionAction.PSEUDONYMIZE,
    confidence_threshold=0.8,
))

profile.add_disposition(EntityDisposition(
    entity_type="CASE_NUMBER",
    action=DispositionAction.KEEP,
    confidence_threshold=0.9,
))

firewall = PrivacyFirewall(profile=profile)
```

### Adding Your Own Custom PII Detectors

There are two approaches depending on whether you need regex rules or a full ML/NLP model.

#### Option A — Regex pattern (no ML, any backend)

Add patterns directly to the catalog at runtime. Works with all detection backends.

```python
import re
from privacy_firewall.patterns.catalog import EntityPattern

# Quick one-liner helper
firewall.add_custom_regex(
    entity_type="EMPLOYEE_ID",
    regex=r"\bEMP-\d{6}\b",
    locales=["GLOBAL"],          # or ["US"], ["ES"], etc.
    confidence=0.95,
    context_words=["employee", "staff"],
    disposition_action="redact", # keep / redact / pseudonymize / mask …
)

# Or build the full EntityPattern object for more control
firewall.add_custom_pattern(EntityPattern(
    entity_type="CASE_NUMBER",
    locale="ES",
    pattern=re.compile(r"\bEXP-\d{4}/\d{6}\b"),
    confidence=0.98,
    context_words=("expediente", "exp"),
    description="Spanish legal case number",
))
```

#### Option B — Custom NLP/ML recognizer (Presidio backend)

Pass your own Presidio `EntityRecognizer` (or `PatternRecognizer`) when creating the firewall.
This is the right approach when you want to use a spaCy model, a transformer, or any custom heuristic.

```python
from privacy_firewall import create_firewall
from privacy_firewall.presidio_integration import create_custom_recognizer

# Helper that wraps a regex list into a Presidio PatternRecognizer
employee_recognizer = create_custom_recognizer(
    entity_type="EMPLOYEE_ID",
    patterns=[r"\bEMP\d{6}\b"],
    context_words=["employee", "badge"],
    score=0.9,
)

firewall = create_firewall(
    domain="generic",
    detector_backend="presidio",   # required for this approach
    custom_recognizers=[employee_recognizer],
)
```

For a fully custom ML-based recognizer, subclass Presidio's `EntityRecognizer` and pass the instance the same way:

```python
from presidio_analyzer import EntityRecognizer, RecognizerResult

class MyModelRecognizer(EntityRecognizer):
    """Example: wraps any ML model as a Presidio recognizer."""

    def load(self): ...

    def analyze(self, text, entities, nlp_artifacts):
        results = []
        # call your model here and yield RecognizerResult objects
        for span in my_model.predict(text):
            results.append(RecognizerResult(
                entity_type="CUSTOM_ENTITY",
                start=span.start,
                end=span.end,
                score=span.confidence,
            ))
        return results

firewall = create_firewall(
    domain="generic",
    detector_backend="presidio",
    custom_recognizers=[MyModelRecognizer(supported_entities=["CUSTOM_ENTITY"])],
)
```

#### Which option to use?

| Scenario | Approach |
|---|---|
| Regex or rule-based custom entity | Option A — `add_custom_regex` / `add_custom_pattern` |
| Locale-specific ID format (new country) | Option A with the matching locale code |
| Existing HuggingFace / spaCy NER model | Option B — wrap in `EntityRecognizer` subclass |
| Complex heuristic or external API call | Option B — implement `analyze()` freely |

### Testing a HuggingFace PII Model

The library has a built-in `transformers` backend. The quickest way to try any HuggingFace NER model is:

```bash
pip install "pii-firewall[transformers]"
```

```python
from privacy_firewall import create_firewall

# Pass any HuggingFace model ID — downloaded automatically on first call
firewall = create_firewall(
    "healthcare",
    detector_backend="transformers",
    transformer_model_id="dslim/bert-base-NER",  # swap for any HF model ID
)

result = firewall.process(
    text="John Doe, SSN 123-45-6789, prescribed enalapril 10mg",
    context={"tenant_id": "t1", "case_id": "c1", "thread_id": "th1", "actor_id": "a1"},
)
print(result.sanitized_text)
```

#### Curated model catalog

The library ships a pre-vetted catalog of models in `transformers_ner/models.py`:

```python
from privacy_firewall.transformers_ner.models import get_model_for_domain

config = get_model_for_domain("medical", "en")
firewall = create_firewall("healthcare", detector_backend="transformers", transformer_model_id=config.model_id)
```

| Domain | Language | Model |
|---|---|---|
| General | `en` | `dslim/bert-base-NER` |
| General | multilingual | `Davlan/xlm-roberta-base-ner-hrl` |
| General | `fr` | `Jean-Baptiste/camembert-ner` |
| Medical | `en` | `d4data/biomedical-ner-all` |
| Medical | `es` | `PlanTL-GOB-ES/bsc-bio-ehr-es` |

#### Run on GPU

```python
firewall = create_firewall(
    "healthcare",
    detector_backend="transformers",
    transformer_model_id="d4data/biomedical-ner-all",
    transformer_device=0,   # 0 = first GPU, -1 = CPU (default)
)
```

#### Combine with regex patterns (Presidio hybrid)

If you need to mix the HF model with regex patterns in the same pipeline, wrap it as a Presidio recognizer:

```python
from presidio_analyzer import EntityRecognizer, RecognizerResult
from transformers import pipeline

class HFPIIRecognizer(EntityRecognizer):
    def __init__(self, model_id: str):
        super().__init__(supported_entities=["PERSON", "ORGANIZATION", "LOCATION"])
        self._pipe = pipeline("ner", model=model_id, aggregation_strategy="simple")

    def load(self): pass

    def analyze(self, text, entities, nlp_artifacts):
        return [
            RecognizerResult(
                entity_type=span["entity_group"],
                start=span["start"],
                end=span["end"],
                score=span["score"],
            )
            for span in self._pipe(text)
        ]

firewall = create_firewall(
    "healthcare",
    detector_backend="presidio",
    custom_recognizers=[HFPIIRecognizer("dslim/bert-base-NER")],
)
```

### Reversible Pseudonymization

```python
# Anonymize
result = firewall.process(text="Contact John Doe at john@example.com", context={...})
print(result.sanitized_text)
# "Contact PERSON_1 at EMAIL_1"

# LLM processes anonymized text
llm_response = "PERSON_1 should verify EMAIL_1 is correct"

# Rehydrate (restore original values)
from privacy_firewall.anonymization_engine import rehydrate_text
mapping = firewall.vault.get_case_mapping(
    tenant_id="...",
    case_id="...",
    thread_id="...",
)
final = rehydrate_text(llm_response, mapping)
print(final)
# "John Doe should verify john@example.com is correct"
```

### Provider-Agnostic SDK Flow

```python
from privacy_firewall import PrivacyFirewallSDK

sdk = PrivacyFirewallSDK.create(domain="healthcare", detector_backend="presidio")

context = {
    "tenant_id": "hospital-001",
    "case_id": "patient-123",
    "thread_id": "consultation-1",
    "actor_id": "doctor-456",
}

# 1) Anonymize input
anon = sdk.anonymize_text(text="Contact John Doe at john@example.com", context=context)

# 2) Call any model client (callable or object with .generate)
def my_llm(prompt: str) -> str:
    return f"Please verify PERSON_1 at EMAIL_1. Input was: {prompt}"

# 3) Rehydrate output
result = sdk.secure_call(
    text="Contact John Doe at john@example.com",
    context=context,
    llm_client=my_llm,
)
print(result.final_text)
```

### GDPR Compliance (Right to be Forgotten)

```python
# Forget all data for a case
deleted = firewall.forget(
    tenant_id="hospital-001",
    case_id="patient-123",
    thread_id="consultation-1",
)
print(f"Deleted {deleted} mappings")
```

## 🚀 Web API

Run the FastAPI web server:

```bash
cd pii-firewall
uvicorn privacy_firewall.web.app:create_app --factory --reload --port 8080
```

Access the API at http://127.0.0.1:8080/docs

### API Example

```bash
curl -X POST "http://localhost:8000/api/run" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Ana García, 43 años, hipertensión",
    "tenant_id": "hospital-001",
    "case_id": "patient-123",
    "thread_id": "thread-1",
    "actor_id": "doctor-456",
    "profile": "healthcare",
        "detector_backend": "gliner"
  }'
```

### Web UI

The project includes a Next.js web interface:

```bash
cd ../pii-web-next
npm install
npm run dev
```

Access at http://127.0.0.1:3010

## 📊 Performance

- **Language detection**: 1–2 ms (first message), 0 ms (cached)
- **Pattern matching (regex mode)**: < 1 ms
- **Presidio NER**: 50–200 ms (depends on text length)
- **OPF / Nemotron**: 50–300 ms
- **Transformer NER**: 100–500 ms (use for accuracy, not latency)
- **Overall round-trip** (Presidio mode): ~50–250 ms per request

### Detection backend comparison

| Backend | Install | Best for | Latency |
|---|---|---|---|
| `regex` | *(none)* | Structured IDs, emails, phones | < 1 ms |
| `presidio` | `[presidio,langdetect]` | Named entities — best speed/accuracy balance | 50–200 ms |
| `hybrid` | `[presidio,langdetect]` | Regex + Presidio for max coverage | 50–250 ms |
| `gliner` | `[gliner]` | Zero-shot NER, no fine-tuning needed | 100–400 ms |
| `transformers` | `[transformers]` | Biomedical NER (d4data, BC5CDR) | 100–500 ms |
| `opf` | `[opf]` | Token-level classifier, language-agnostic | 50–200 ms |
| `nemotron` | `[opf]` | NVIDIA fine-tune, high recall on free text | 100–300 ms |

**Optimization tips**:
- Use thread-level language caching (enabled by default)
- Use `detector_backend="presidio"` for best speed/accuracy balance

## 🏗️ Architecture

```
src/privacy_firewall/
├── language/              # Auto-detection & routing
│   ├── detector.py       # LanguageDetector (langdetect/fasttext)
│   └── router.py         # LanguageRouter (spaCy model selection)
├── patterns/             # Locale-aware patterns
│   ├── catalog.py        # PatternCatalog
│   └── locales/          # ONE FILE PER LANGUAGE ✨
│       ├── global_patterns.py
│       ├── es_patterns.py
│       ├── us_patterns.py
│       ├── fr_patterns.py
│       ├── de_patterns.py
│       ├── it_patterns.py
│       └── pt_patterns.py
├── profiles/             # Domain profiles
│   ├── profiles.py       # DomainProfile, EntityDisposition
│   └── presets.py        # HEALTHCARE, FINANCE, LEGAL
├── presidio_integration/ # Full Presidio capabilities
│   ├── engine.py         # Analyzer + Anonymizer
│   └── recognizers.py    # Custom recognizers
├── transformers_ner/     # Domain-specific models
│   ├── engine.py         # TransformerNEREngine
│   └── models.py         # Biomedical NER model catalog
├── unified_detector.py   # Multi-backend orchestration
├── anonymization_engine.py  # Disposition-based anonymization
├── firewall.py        # Next-gen PrivacyFirewall
└── web/                  # FastAPI web interface
    └── app.py            # REST API
```

## 🆚 Comparison

| Feature | Privacy Firewall | Presidio | scrubadub | AWS Comprehend |
|---------|---------------------|----------|-----------|----------------|
| **Domain awareness** | ✅ Keep relevant data | ❌ | ❌ | ⚠️ Healthcare only |
| **Multi-language** | ✅ 55+ auto-detect | ✅ Manual | ❌ English only | ✅ Some |
| **Locale patterns** | ✅ Per-country | ❌ | ❌ | ❌ |
| **Multiple dispositions** | ✅ | ❌ Basic | ❌ | ❌ |
| **Transformers** | ✅ BioBERT, biomedical NER | ❌ | ❌ | ✅ Proprietary |
| **Reversibility** | ✅ Vault | ❌ | ❌ | ❌ |
| **Custom patterns** | ✅ Runtime | ⚠️ Code | ⚠️ Code | ❌ |
| **Thread caching** | ✅ 0ms after first | ❌ | ❌ | N/A |
| **Open source** | ✅ | ✅ | ✅ | ❌ |

## 🔌 Extending with New Locales

Add support for a new country in 3 steps:

1. **Create pattern file** (`patterns/locales/nl_patterns.py`):
```python
import re
from ..catalog import EntityPattern

NL_BSN = EntityPattern(
    entity_type="NATIONAL_ID",
    locale="NL",
    pattern=re.compile(r"\b\d{9}\b"),
    confidence=0.9,
    context_words=("bsn", "burgerservicenummer"),
    description="Dutch BSN",
)

NL_PATTERNS = [NL_BSN]
```

2. **Import in** `patterns/locales/__init__.py`:
```python
from .nl_patterns import NL_PATTERNS
LOCALE_PATTERNS = [...] + NL_PATTERNS
```

3. **Add language config** (optional, for spaCy models):
```python
# In language/router.py
"nl": LanguageConfig(
    language_code="nl",
    spacy_model="nl_core_news_sm",
    patterns_locale="NL",
),
```

Done! Dutch patterns now available automatically.

## 📚 Documentation

- **[Developer Guide (HTML)](docs/guide.html)** - Complete implementation and usage guide
- **[tests_integration/README.md](tests_integration/README.md)** - Integration test notes

To show the guide in a panel in VS Code:
1. Open **[docs/guide.html](docs/guide.html)**
2. Select Open Preview (or use Ctrl+Shift+V)

## 🧪 Testing

```bash
# Unit tests
pytest tests/

# Integration tests
pytest tests_integration/

# Quick package smoke test
python -c "import privacy_firewall; print('ok')"
```

## 🔐 Security & Privacy

- ✅ Simple end-to-end anonymize→LLM→rehydrate flow
- ✅ Reversible pseudo-anonymization with vault
- ✅ Pluggable vault storage (in-memory and SQLite)
- ✅ GDPR "right to be forgotten"
- ✅ Audit trails in `result.trace`
- ✅ No data leaves your infrastructure

## 📝 License

Apache 2.0 — see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions welcome! Areas to contribute:
- New locale patterns (add your country!)
- Domain profiles (education, government, etc.)
- Custom recognizers
- Performance optimizations
- Documentation improvements

## 🙏 Acknowledgments

Built with:
- [Presidio](https://github.com/microsoft/presidio) - Microsoft's PII detection library
- [spaCy](https://spacy.io/) - Industrial-strength NLP
- [langdetect](https://github.com/Mimino666/langdetect) - Fast language detection
- [transformers](https://huggingface.co/transformers/) - State-of-the-art NLP models

---

**Built with ❤️ for privacy-first AI applications**
