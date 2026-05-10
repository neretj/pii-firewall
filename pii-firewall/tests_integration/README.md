# Integration Test Suite

Structured and maintainable E2E tests for Privacy Firewall.

## Folder structure

- tests_integration/conftest.py: shared fixtures (firewall fixtures + API client)
- tests_integration/common/frontend_queries.py: loads predefined frontend prompts directly from pii-web-next/lib/constants.ts
- tests_integration/common/e2e_matrix.py: reusable matrix runner for profiles, engines, mapping, and rehydration checks
- tests_integration/languages/: one test module per language

## Coverage goals

1. Test per language: Spanish, English, French, German, Italian, Portuguese.
2. Each language test runs all predefined frontend queries.
3. Each language test runs across all detection engines:
   - regex, presidio, opf, gliner, nemotron, transformers, hybrid
   - engines unavailable in the current environment are auto-detected and skipped.
4. Mapping and rehydration are validated end-to-end via /api/run and /api/forget.

## Run

Run all integration tests:

```bash
python -m pytest tests_integration -v
```

Run only language suites:

```bash
python -m pytest tests_integration/languages -v
```

Run one language:

```bash
python -m pytest tests_integration/languages/test_spanish.py -v
```
