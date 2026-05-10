# PII Firewall

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A best-in-class, multi-language, domain-aware **PII anonymization library** for AI applications. It intercepts text before it reaches an LLM, strips or transforms sensitive data, forwards the sanitized prompt, and then re-hydrates the model response — all transparently.

---

## What it does

### Detect → Anonymize → Rehydrate

```
User text  ──→  [ PII Firewall ]  ──→  Sanitized prompt  ──→  LLM
                      │                                          │
                 Secure vault                             Model response
                      │                                          │
                      └──────────  Re-hydrated reply  ←─────────┘
```

1. **Detect** PII entities using one or more configurable backends (regex patterns, Presidio/spaCy, OPF, GLiNER-PII, Nemotron, Transformers NER).
2. **Anonymize** each entity according to the active domain profile — redact, pseudonymize, generalize, mask, hash, or suppress.
3. **Rehydrate** the model's reply by substituting tokens back from an encrypted in-memory vault, so the end-user sees real values while the LLM never did.

### Key capabilities

| Feature | Details |
|---|---|
| **Domain profiles** | Built-in presets for Healthcare, Finance, and Legal; fully customizable |
| **Domain-aware keep rules** | Medical terms, transaction amounts, legal references, etc. are *kept* — not redacted |
| **7 disposition actions** | Keep, Redact, Pseudonymize, Generalize, Mask, Hash, Suppress |
| **Reversible pseudonymization** | Secure vault stores the original→token mapping for rehydration |
| **55+ language auto-detection** | Thread-level caching adds zero latency after the first call |
| **Locale-specific patterns** | Spanish DNI, US SSN, French INSEE, German Personalausweis, Italian CF, Portuguese NIF, and more |
| **Multiple detection backends** | Mix and match: regex, Presidio, OPF, GLiNER, Nemotron, Transformers |
| **Full audit trace** | Every call produces a `TraceRecord` with detected entities, replacements, and language |

### Domain profile examples

**Healthcare** — keeps diagnoses and medications, redacts personal identifiers, generalizes ages and dates:
```python
from privacy_firewall import create_firewall

firewall = create_firewall("healthcare")
result = firewall.process(
    text="Ana García, 43 años, hipertensión. Prescripción: enalapril 10mg.",
    context={"tenant_id": "hospital-001", "case_id": "patient-123",
              "thread_id": "consultation-1", "actor_id": "doctor-456"},
)
print(result.sanitized_text)
# → "PERSON_1, [AGE_40-49], hipertensión. enalapril 10mg."
# Medical terms (hipertensión, enalapril) are preserved!
```

**Finance** — keeps amounts and account types, masks card numbers, pseudonymizes account numbers:
```python
firewall = create_firewall("finance")
```

**Legal** — pseudonymizes party names, generalizes dates to year, redacts strong identifiers:
```python
firewall = create_firewall("legal")
```

---

## Repository structure

```text
pii-firewall-clean/
  pii-firewall/    # Python library, FastAPI REST API, and HTML guide
  pii-web-next/    # Next.js playground UI (anonymize → LLM → rehydrate)
```

---

## Prerequisites

- Python 3.10+
- Node.js 18+

---

## 1. Run the backend API

```bash
cd pii-firewall
python -m pip install --upgrade pip
python -m pip install -e ".[web,presidio,langdetect]"
uvicorn privacy_firewall.web.app:create_app --factory --reload --port 8080
```

- Interactive API docs: http://127.0.0.1:8080/docs
- Full guide (HTML): [pii-firewall/docs/guide.html](pii-firewall/docs/guide.html)

> **VS Code tip:** open [pii-firewall/docs/guide.html](pii-firewall/docs/guide.html) and press `Ctrl+Shift+V` to preview it.

---

## 2. Run the frontend playground

```bash
cd pii-web-next
Copy-Item .env.example .env.local   # Windows (PowerShell)
# cp .env.example .env.local        # macOS / Linux
npm install
npm run dev
```

UI: http://127.0.0.1:3010

The frontend talks to the backend via `PII_API_BASE_URL` in `pii-web-next/.env.local`. The default (`http://127.0.0.1:8080`) works out of the box.

---

## 3. Use as a library

**Local development install:**

```bash
cd pii-firewall
pip install -e .
```

**Install from PyPI:**

```bash
# Minimal (pattern-based only)
pip install pii-firewall

# Recommended (Presidio + language detection)
pip install "pii-firewall[presidio,langdetect]"

# Full feature set (Transformers, OPF, GLiNER)
pip install "pii-firewall[all]"
```

---

## License

Apache 2.0. See [pii-firewall/LICENSE](pii-firewall/LICENSE).
