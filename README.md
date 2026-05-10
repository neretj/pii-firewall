# PII Firewall

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![CI](https://img.shields.io/badge/CI-passing-brightgreen.svg)](#)
[![PyPI](https://img.shields.io/pypi/v/pii-firewall.svg)](https://pypi.org/project/pii-firewall/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/pii-firewall.svg)](https://pypi.org/project/pii-firewall/)

Open-source PII firewall for LLM apps. Detect, anonymize and rehydrate sensitive data before it reaches OpenAI, Anthropic or any LLM provider.

```
pip install "pii-firewall[presidio,langdetect]"
```

> **Try the playground:** run `pii-web-next` locally .
---

## Repository structure

```
/pii-firewall     Python SDK + FastAPI server
/pii-web-next     Playground UI (Next.js)
```

---

## How it works

### Detect → Anonymize → Rehydrate

```
User text  ──→  [ PII Firewall ]  ──→  Sanitized prompt  ──→  LLM
                      │                                          │
                 Secure vault                             Model response
                      │                                          │
                      └──────────  Re-hydrated reply  ←─────────┘
```

1. **Detect** — finds PII entities using one or more configurable backends (regex patterns, Presidio/spaCy, OPF, GLiNER-PII, Nemotron, Transformers NER).
2. **Anonymize** — transforms each entity according to the active domain profile: redact, pseudonymize, generalize, mask, hash, or suppress.
3. **LLM call** — the sanitized prompt is forwarded to any LLM. The model never sees real personal data.
4. **Rehydrate** — the model's response is restored by substituting tokens back from a secure in-memory vault, so the end-user sees real values.

### Key capabilities

| Feature | Details |
|---|---|
| **Domain profiles** | Built-in presets for Healthcare, Finance, Legal, and Generic; fully customizable |
| **Domain-aware keep rules** | Medical terms (diagnoses, medications, procedures) are *kept* — not redacted — in healthcare and related profiles |
| **7 disposition actions** | Keep, Redact, Pseudonymize, Generalize, Mask, Hash, Suppress |
| **Reversible pseudonymization** | Secure vault stores the original→token mapping for rehydration |
| **55+ language auto-detection** | Thread-level caching adds zero latency after the first call |
| **Locale-specific patterns** | Spanish DNI, US SSN, French INSEE, German Personalausweis, Italian CF, Portuguese NIF, and more |
| **Multiple detection backends** | regex, Presidio, Hybrid, GLiNER, Transformers, OPF, Nemotron — switch with one parameter |
| **Streaming support** | `secure_call_stream()` yields rehydrated tokens in real-time for SSE/WebSocket apps |
| **Full audit trace** | Every call produces a `TraceRecord` with detected entities, replacements, and language |
| **GDPR right to forget** | Single call to wipe all vault mappings for a case or thread |

---

## Use cases

| Scenario | Profile | Key benefit |
|---|---|---|
| Protect patient data before sending clinical notes to GPT-4 | `healthcare` | Medical terms kept; patient identifiers stripped |
| Redact Spanish DNI, NIE and IBAN before LLM calls | `healthcare` / `finance` | Locale-aware patterns for ES/EU documents |
| Rehydrate LLM responses without leaking real names | any | Vault restores original values transparently |
| GDPR Art. 17 right-to-forget for LLM conversation history | any | `firewall.forget()` wipes all mappings by thread/case |
| Customer support: anonymize tickets before sending to AI | `generic` | Zero PII reaches the model provider |
| Legal discovery: pseudonymize party names in documents | `legal` | Reversible — case management still works |

---

## Quick start

```bash
pip install "pii-firewall[presidio,langdetect]"
python -m spacy download en_core_web_sm
```

```python
from privacy_firewall import create_firewall

firewall = create_firewall("healthcare")

result = firewall.process(
    text="Patient John Doe, SSN 123-45-6789, diagnosed with hypertension. Prescribed lisinopril 10mg.",
    context={
        "tenant_id": "hospital-001",
        "case_id":   "patient-123",
        "thread_id": "consultation-1",
        "actor_id":  "doctor-456",
    },
)

print(result.sanitized_text)
# → "Patient PERSON_1, [REDACTED], diagnosed with hypertension. Prescribed lisinopril 10mg."
#   Medical terms (hypertension, lisinopril) are preserved — the LLM still understands the case.

print(result.final_text)
# → After the LLM responds, real names are restored for the end-user.
```

---

## Integrations

PII Firewall wraps any callable or object that accepts a text prompt. Below are drop-in recipes for the most common providers.

### OpenAI

```python
from openai import OpenAI
from privacy_firewall import create_firewall

client = OpenAI()
firewall = create_firewall("healthcare", detector_backend="presidio")

context = {"tenant_id": "acme", "case_id": "c1", "thread_id": "t1", "actor_id": "u1"}

def openai_llm(prompt: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content

result = firewall.secure_call(text=user_input, context=context, llm_client=openai_llm)
print(result.final_text)  # real names restored
```

### Anthropic

```python
import anthropic
from privacy_firewall import create_firewall

ac = anthropic.Anthropic()
firewall = create_firewall("healthcare", detector_backend="presidio")

def anthropic_llm(prompt: str) -> str:
    msg = ac.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text

result = firewall.secure_call(text=user_input, context=context, llm_client=anthropic_llm)
```

### LangChain

```python
from langchain_openai import ChatOpenAI
from privacy_firewall import create_firewall

llm = ChatOpenAI(model="gpt-4o")
firewall = create_firewall("generic", detector_backend="presidio")

def langchain_llm(prompt: str) -> str:
    return llm.invoke(prompt).content

result = firewall.secure_call(text=user_input, context=context, llm_client=langchain_llm)
```

### FastAPI middleware

```python
from fastapi import FastAPI
from privacy_firewall import PrivacyFirewallSDK

app = FastAPI()
sdk = PrivacyFirewallSDK.create(domain="healthcare", detector_backend="presidio")

@app.post("/chat")
async def chat(req: dict):
    context = req["context"]
    anon = sdk.anonymize_text(text=req["message"], context=context)
    llm_response = await call_your_llm(anon.sanitized_text)
    final = sdk.rehydrate_text(text=llm_response, context=context)
    return {"response": final}
```

### Streaming (SSE / WebSocket)

```python
# Yields rehydrated tokens as they stream from the LLM — no buffering needed
for token in firewall.secure_call_stream(text=user_input, context=context, llm_client=streaming_llm):
    yield token
```

---

## Domain profiles

The active profile controls what happens to each detected entity type.

### Healthcare

Keeps clinical data the LLM needs. Strips personal identifiers.

```python
firewall = create_firewall("healthcare")
result = firewall.process(
    text="Ana García, 43 años, hipertensión. Prescripción: enalapril 10mg.",
    context={...},
)
print(result.sanitized_text)
# → "PERSON_1, [AGE_40-49], hipertensión. enalapril 10mg."
#   Diagnosis and medication are preserved. Name and age are anonymized.
```

### Finance

Keeps amounts and transaction context. Masks card numbers. Pseudonymizes account numbers (reversible).

```python
firewall = create_firewall("finance")
result = firewall.process(
    text="Cliente María López, tarjeta 4111111111111111, transferencia de 2.500€ a cuenta ES12345678.",
    context={...},
)
print(result.sanitized_text)
# → "Cliente PERSON_1, tarjeta 4111...1111, transferencia de 2.500€ a cuenta ACCOUNT_1."
#   Amount is preserved for the LLM. Card and account are masked/pseudonymized.
```

### Legal

High anonymity. Pseudonymizes party names. Generalizes all dates to year only.

```python
firewall = create_firewall("legal")
result = firewall.process(
    text="El demandante Juan Pérez presentó recurso el 15 de marzo de 2024, expediente EXP-2024/001234.",
    context={...},
)
print(result.sanitized_text)
# → "El demandante PERSON_1 presentó recurso en 2024, expediente EXP-2024/001234."
#   Case number kept. Party name pseudonymized. Date generalized to year.
```

### Custom profile

```python
from privacy_firewall import create_firewall, create_custom_profile, EntityDisposition, DispositionAction

profile = create_custom_profile("my_domain")
profile.add_disposition(EntityDisposition(
    entity_type="EMPLOYEE_ID",
    action=DispositionAction.REDACT,
    confidence_threshold=0.9,
))
profile.add_disposition(EntityDisposition(
    entity_type="PROJECT_CODE",
    action=DispositionAction.KEEP,
    confidence_threshold=0.8,
))

firewall = create_firewall("generic", profile=profile)
```

---

## Multi-language support

Language is detected automatically per message. No configuration needed.

```python
firewall = create_firewall("healthcare")

# Spanish
result = firewall.process(text="Paciente con diabetes tipo 2, DNI 12345678A", context={...})

# English
result = firewall.process(text="Patient with type 2 diabetes, SSN 123-45-6789", context={...})

# French
result = firewall.process(text="Patient avec diabète, INSEE 1234567890123", context={...})
```

Locale-specific patterns are applied automatically: Spanish DNI/NIE, US SSN/EIN, French INSEE/SIREN, German Steuernummer, Italian Codice Fiscale, Portuguese NIF, and global fallbacks for all other languages.

---

## Detection backends

| Backend | Install extra | Best for | Latency |
|---|---|---|---|
| `regex` | *(none)* | Structured IDs, emails, phones | < 1 ms |
| `presidio` | `[presidio,langdetect]` | Named entities (persons, orgs) — best balance | 50–200 ms |
| `hybrid` | `[presidio,langdetect]` | Regex + Presidio combined for max coverage | 50–250 ms |
| `gliner` | `[gliner]` | Zero-shot NER, no fine-tuning needed | 100–400 ms |
| `transformers` | `[transformers]` | Biomedical NER (`d4data`, BC5CDR) — highest accuracy for medical entities | 100–500 ms |
| `opf` | `[opf]` | Token-level PII classifier, language-agnostic | 50–200 ms |
| `nemotron` | `[opf]` | NVIDIA fine-tune on OPF — high recall on free text | 100–300 ms |

```python
firewall = create_firewall("healthcare", detector_backend="presidio")
```

---

## Adding custom PII detectors

### Option A — Regex rule (any backend)

```python
firewall.add_custom_regex(
    entity_type="EMPLOYEE_ID",
    regex=r"\bEMP-\d{6}\b",
    locales=["GLOBAL"],
    confidence=0.95,
    context_words=["employee", "staff"],
    disposition_action="redact",
)
```

### Option B — HuggingFace / ML model (Presidio backend)

```python
from privacy_firewall import create_firewall
from privacy_firewall.presidio_integration import create_custom_recognizer

recognizer = create_custom_recognizer(
    entity_type="EMPLOYEE_ID",
    patterns=[r"\bEMP\d{6}\b"],
    context_words=["employee", "badge"],
    score=0.9,
)

firewall = create_firewall("generic", detector_backend="presidio", custom_recognizers=[recognizer])
```

For a fully custom ML model, subclass Presidio's `EntityRecognizer`:

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
            RecognizerResult(entity_type=s["entity_group"], start=s["start"], end=s["end"], score=s["score"])
            for s in self._pipe(text)
        ]

firewall = create_firewall("healthcare", detector_backend="presidio",
                           custom_recognizers=[HFPIIRecognizer("dslim/bert-base-NER")])
```

### Testing a HuggingFace NER model directly

```bash
pip install "pii-firewall[transformers]"
```

```python
# Built-in catalog of domain models
from privacy_firewall.transformers_ner.models import get_model_for_domain

config = get_model_for_domain("medical", "en")  # → d4data/biomedical-ner-all
firewall = create_firewall("healthcare", detector_backend="transformers",
                           transformer_model_id=config.model_id,
                           transformer_device=0)  # 0 = GPU, -1 = CPU
```

Available catalog entries: `("general", "en")`, `("medical", "en")`, `("medical", "es")`, and multilingual.

---

## SDK pattern (provider-agnostic)

`PrivacyFirewallSDK` wraps the firewall with convenience methods for building LLM middleware:

```python
from privacy_firewall import PrivacyFirewallSDK

sdk = PrivacyFirewallSDK.create(domain="healthcare", detector_backend="presidio")

context = {"tenant_id": "hospital-001", "case_id": "patient-123",
           "thread_id": "thread-1", "actor_id": "doctor-456"}

# Anonymize only
anon = sdk.anonymize_text(text="John Doe, SSN 123-45-6789", context=context)
print(anon.sanitized_text)  # "PERSON_1, [REDACTED]"

# Full round-trip with any LLM client
def my_llm(prompt: str) -> str:
    ...  # call OpenAI, Anthropic, Ollama, etc.

result = sdk.secure_call(text="John Doe has hypertension.", context=context, llm_client=my_llm)
print(result.sanitized_text)  # What the LLM saw
print(result.final_text)      # Restored output shown to the user

# Anonymize/rehydrate whole JSON payloads (deep-walks strings recursively)
safe_payload = sdk.anonymize_payload(payload={"patient": "Ana García", "notes": ["DNI: 12345678A"]}, context=context)
```

---

## Persistent vault & GDPR

By default, the vault is in-memory. For persistence across restarts:

```python
from privacy_firewall import create_firewall, SQLiteMappingVault

vault = SQLiteMappingVault("privacy_vault.db")
firewall = create_firewall("healthcare", vault=vault)
```

To comply with GDPR Art. 17 (right to erasure):

```python
deleted = firewall.forget(tenant_id="hospital-001", case_id="patient-123", thread_id="thread-1")
print(f"Deleted {deleted} token mappings")
# After this, the LLM response can no longer be rehydrated for this thread.
```

---

## Running the stack

### Prerequisites

- Python 3.10+
- Node.js 18+

### 1. Backend API

```bash
cd pii-firewall
python -m pip install --upgrade pip
python -m pip install -e ".[web,presidio,langdetect]"
uvicorn privacy_firewall.web.app:create_app --factory --reload --port 8080
```

- Interactive API docs: http://127.0.0.1:8080/docs
- Full developer guide: [pii-firewall/docs/guide.html](pii-firewall/docs/guide.html)

> **VS Code tip:** open [pii-firewall/docs/guide.html](pii-firewall/docs/guide.html) and press `Ctrl+Shift+V` to preview it.

### 2. Frontend playground

```bash
cd pii-web-next
Copy-Item .env.example .env.local   # Windows PowerShell
# cp .env.example .env.local        # macOS / Linux
npm install
npm run dev
```

UI: http://127.0.0.1:3010

The frontend proxies to the backend via `PII_API_BASE_URL` in `pii-web-next/.env.local` (default: `http://127.0.0.1:8080`).

### 3. Library only

```bash
# From this repo
cd pii-firewall && pip install -e .

# From PyPI
pip install pii-firewall                             # minimal (regex only)
pip install "pii-firewall[presidio,langdetect]"      # recommended
pip install "pii-firewall[all]"                      # full feature set
```

---

## License

Apache 2.0. See [pii-firewall/LICENSE](pii-firewall/LICENSE).
