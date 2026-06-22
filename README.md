# PII Firewall

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![PyPI](https://img.shields.io/pypi/v/pii-firewall.svg)](https://pypi.org/project/pii-firewall/)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/pii-firewall?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/pii-firewall)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/neretj/pii-firewall/blob/main/pii-firewall/docs/pii_firewall_demo.ipynb)

**Stop leaking PII into LLM APIs without breaking conversation context.**

PII Firewall intercepts sensitive data before it reaches OpenAI, Anthropic, or any model provider, then restores it transparently in the response.

```
User text  ──►  [ PII Firewall ]  ──►  Sanitized prompt  ──►  LLM
                      │                                          │
                 Secure vault                             Model response
                      │                                          │
                      └──────────  Re-hydrated reply  ◄─────────┘
```

Standard redaction breaks context — replacing `"John"` with `[REDACTED]` means the model can no longer refer to the person by name. PII Firewall uses a stateful **Detect → Anonymize → Rehydrate** flow so the LLM sees pseudonyms while the user gets real answers.

---

## Try it in 30 seconds (no ML models needed)

```bash
pip install pii-firewall
```

```python
from privacy_firewall import create_firewall

firewall = create_firewall("healthcare", detector_backend="regex")

result = firewall.secure_call(
    text="Patient John Doe, SSN 123-45-6789, diagnosed with hypertension.",
    context={
        "tenant_id": "hospital-001",
        "case_id":   "patient-123",
        "thread_id": "consultation-1",
        "actor_id":  "doctor-456",
    },
    llm_client=lambda prompt: f"Acknowledged for {prompt[:30]}..."
)

print(result.sanitized_text)  # Patient PERSON_1, SSN_REDACTED, diagnosed with hypertension.
print(result.final_text)      # Patient John Doe, SSN 123-45-6789, diagnosed with hypertension.
```

> **Note:** The package is published as `pii-firewall` on PyPI; the import namespace is `privacy_firewall`.

---

## Why PII Firewall?

| Problem | How PII Firewall handles it |
|---|---|
| `[REDACTED]` breaks LLM context | Reversible pseudonyms (`PERSON_1`, `EMAIL_1`) keep context intact |
| Different PII needs different treatment | 6 disposition actions: pseudonymize, mask, hash, generalize, redact, keep |
| Spanish/French/German/etc. IDs | Locale-specific patterns for 55+ languages |
| Hard to audit what left your system | Vault + GDPR right-to-forget + TTL |
| Streaming chat needs real-time protection | Rehydrates tokens on the fly |

---

## Quick start with real detection (Presidio)

```bash
pip install "pii-firewall[presidio,langdetect]"
python -m spacy download en_core_web_sm
```

```python
from privacy_firewall import create_firewall

firewall = create_firewall("finance", detector_backend="presidio")

result = firewall.secure_call(
    text="Card ending 4242 belongs to john@example.com.",
    context={"tenant_id": "acme", "case_id": "c1", "thread_id": "t1", "actor_id": "u1"},
    llm_client=lambda prompt: f"Processed: {prompt}"
)

print(result.sanitized_text)  # Card ending MASKED_4242 belongs to EMAIL_1.
print(result.final_text)      # Card ending 4242 belongs to john@example.com.
```

### Pick your domain profile

| Profile | Behaviour |
|---|---|
| `healthcare` | Pseudonymizes patient identifiers; keeps diagnoses, medications, procedures |
| `finance` | Masks card numbers; pseudonymizes account numbers and IBANs; keeps amounts |
| `legal` | High anonymity; pseudonymizes party names; generalizes dates to month/year |
| `generic` | Balanced defaults for any use case |

---

## Real-world use cases

### Healthcare chatbot
A patient asks: *"I'm John Doe, born 1985-03-12, my SSN is 123-45-6789."*

The LLM receives: *"I'm PERSON_1, born YEAR_1980_1989, my SSN is REDACTED."*

The response is rehydrated before the user sees it.

### Fintech support automation
A support ticket contains IBANs, card numbers, and email addresses. The LLM summarizes the issue without ever seeing real account data.

### Legal document review
Party names, dates, and locations are pseudonymized so teams can run contract analysis through LLMs without exposing client data.

---

## Detection backends

| Backend | Install extra | Best for | Latency |
|---|---|---|---|
| `regex` | *(none)* | Structured IDs, emails, phones — zero dependencies | < 1 ms |
| `presidio` | `[presidio,langdetect]` | Named entities — recommended default | 50–200 ms |
| `hybrid` | `[presidio,langdetect]` | Regex + Presidio for maximum coverage | 50–250 ms |
| `gliner` | `[gliner]` | Zero-shot NER, no fine-tuning needed | 100–400 ms |
| `transformers` | `[transformers]` | Domain-specific models (biomedical, legal) | 100–500 ms |
| `opf` | `[opf]` | OpenAI Privacy Filter — token-level classifier | 50–200 ms |
| `nemotron` | `[opf]` | NVIDIA Nemotron fine-tune on OPF | 100–300 ms |

---

## Documentation & links

- **[Full documentation](https://pii-firewall.com/documentation)**
- **[Interactive demo (Colab)](https://colab.research.google.com/github/neretj/pii-firewall/blob/main/pii-firewall/docs/pii_firewall_demo.ipynb)**
- **[Website](https://pii-firewall.com/)**
- **[PyPI package](https://pypi.org/project/pii-firewall/)**

---

## License

Apache 2.0. See [LICENSE](pii-firewall/LICENSE).
