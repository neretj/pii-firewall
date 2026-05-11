# PII Firewall

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![PyPI](https://img.shields.io/pypi/v/pii-firewall.svg)](https://pypi.org/project/pii-firewall/)

Open-source PII firewall for LLM apps. Intercept sensitive data before it reaches any LLM provider, then restore it transparently in the response.

**[Website](https://pii-firewall.com/) · [Documentation](https://pii-firewall.com/documentation)**

```
pip install "pii-firewall[presidio,langdetect]"
```

<p align="center">
  <img src="assets/demo.gif" alt="PII Firewall demo" width="900" />
</p>

---

## How it works

```
User text  -->  [ PII Firewall ]  -->  Sanitized prompt  -->  LLM
                     |                                          |
                Secure vault                             Model response
                     |                                          |
                     +----------  Re-hydrated reply  <----------+
```

1. **Detect** - finds PII using configurable backends (regex, Presidio, GLiNER, Transformers NER, and more).
2. **Anonymize** - transforms each entity: pseudonymize, generalize, mask, hash, or redact.
3. **LLM call** - the sanitized prompt is forwarded. The model never sees real personal data.
4. **Rehydrate** - the response is restored from a secure in-memory vault before reaching the user.

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
# -> "Patient [PERSON_001], [REDACTED], diagnosed with hypertension. Prescribed lisinopril 10mg."
#    Medical terms (hypertension, lisinopril) are preserved -- the LLM still understands the case.

# After the LLM responds, real names are restored for the end-user:
print(result.final_text)
```

### Profiles

Pick the profile that matches your domain:

| Profile | What it does |
|---|---|
| `healthcare` | Strips patient identifiers; keeps diagnoses, medications, procedures |
| `finance` | Masks card numbers; pseudonymizes account numbers; keeps amounts |
| `legal` | High anonymity; pseudonymizes party names; generalizes dates to year |
| `generic` | Balanced defaults for any domain |

```python
firewall = create_firewall("healthcare")   # or "finance", "legal", "generic"
```

---

## Integrations

### OpenAI / Anthropic / any callable

```python
from openai import OpenAI
from privacy_firewall import create_firewall

client = OpenAI()
firewall = create_firewall("healthcare", detector_backend="presidio")

context = {"tenant_id": "acme", "case_id": "c1", "thread_id": "t1", "actor_id": "u1"}

def my_llm(prompt: str) -> str:
    resp = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
    return resp.choices[0].message.content

result = firewall.secure_call(text=user_input, context=context, llm_client=my_llm)
print(result.final_text)   # real names restored
```

### Streaming (SSE / WebSocket)

```python
for token in firewall.secure_call_stream(text=user_input, context=context, llm_client=streaming_llm):
    yield token
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

---

## Detection backends

| Backend | Install extra | Best for |
|---|---|---|
| `regex` | *(none)* | Structured IDs, emails, phones |
| `presidio` | `[presidio,langdetect]` | Named entities -- recommended default |
| `hybrid` | `[presidio,langdetect]` | Regex + Presidio for maximum coverage |
| `gliner` | `[gliner]` | Zero-shot NER, no fine-tuning |
| `transformers` | `[transformers]` | Biomedical NER -- highest accuracy for medical |
| `nemotron` | `[opf]` | NVIDIA fine-tune, high recall on free text |

```python
firewall = create_firewall("healthcare", detector_backend="presidio")
```

---

## Multi-language support

Language is detected automatically -- no configuration needed. Locale-specific patterns are applied for Spanish DNI/NIE, US SSN/EIN, French INSEE, German Steuernummer, Italian Codice Fiscale, Portuguese NIF, and more.

---

## GDPR right to forget

```python
deleted = firewall.forget(tenant_id="hospital-001", case_id="patient-123", thread_id="thread-1")
print(f"Deleted {deleted} token mappings")
```

---

## Running the playground locally

**Prerequisites:** Python 3.10+, Node.js 18+

### 1 - Backend

```bash
cd pii-firewall
pip install -e ".[web,presidio,langdetect]"
uvicorn privacy_firewall.web.app:create_app --factory --reload --port 8080
```

API docs: http://127.0.0.1:8080/docs

### 2 - Frontend

```bash
cd pii-web-next
cp .env.example .env.local   # macOS/Linux
# Copy-Item .env.example .env.local   # Windows PowerShell
npm install
npm run dev
```

UI: http://127.0.0.1:3010

---

## Repository structure

```
/pii-firewall     Python SDK + FastAPI server
/pii-web-next     Playground UI (Next.js)
```

---

## License

Apache 2.0. See [pii-firewall/LICENSE](pii-firewall/LICENSE).