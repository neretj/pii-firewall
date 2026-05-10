# Contributing to PII Firewall

Thank you for your interest in contributing! PII Firewall is an open-source project and community contributions are very welcome.

## Ways to contribute

- **New locale patterns** — add support for your country's ID formats (see [Adding a new locale](#adding-a-new-locale))
- **Domain profiles** — healthcare, finance, and legal are built-in; PRs for education, government, HR, etc. are welcome
- **Custom recognizers** — wrap a HuggingFace NER model or external API as a Presidio recognizer
- **Bug fixes** — open an issue first for non-trivial bugs so we can discuss the approach
- **Documentation** — improve examples, clarify language, fix typos
- **Performance** — profiling, benchmarks, latency improvements

---

## Development setup

```bash
git clone https://github.com/neretj/llm-pii-firewall.git
cd llm-pii-firewall/pii-firewall

python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.\.venv\Scripts\Activate.ps1     # Windows PowerShell

pip install -e ".[presidio,langdetect,gliner,transformers,dev]"
python -m spacy download en_core_web_sm
python -m spacy download es_core_news_sm
```

## Running tests

```bash
# Unit tests
pytest tests/

# Integration tests (require model downloads)
pytest tests_integration/

# Smoke test
python -c "from privacy_firewall import create_firewall; print('ok')"
```

---

## Adding a new locale

1. Create `pii-firewall/src/privacy_firewall/patterns/locales/nl_patterns.py`:

```python
import re
from ..catalog import EntityPattern

NL_BSN = EntityPattern(
    entity_type="NATIONAL_ID",
    locale="NL",
    pattern=re.compile(r"\b\d{9}\b"),
    confidence=0.9,
    context_words=("bsn", "burgerservicenummer"),
    description="Dutch BSN (Burgerservicenummer)",
)

NL_PATTERNS = [NL_BSN]
```

2. Import in `patterns/locales/__init__.py`:

```python
from .nl_patterns import NL_PATTERNS
LOCALE_PATTERNS = [...existing...] + NL_PATTERNS
```

3. Open a PR and add at least one integration test in `tests_integration/languages/`.

---

## Code style

- Python 3.10+ type hints preferred
- No external runtime dependencies in the base package (extras only)
- New entity recognizers go in `presidio_integration/recognizers.py` or the relevant backend file

## Commit conventions

Use conventional commits when possible:

```
feat: add Dutch BSN pattern
fix: correctly match French INSEE with optional spaces
docs: add LangChain integration example
test: add German Steuernummer integration test
```

---

## Opening a pull request

1. Fork the repo and create a branch from `main`
2. Make your changes with tests
3. Ensure `pytest tests/` passes
4. Open a PR describing what you changed and why

For large changes, please open an issue first so we can discuss the design before you invest time in the implementation.
