# Good first issues for pii-firewall

Create these issues in GitHub to attract contributors and signal that the project is active.

## Issue 1: Add Dutch (NL) locale patterns
**Title:** `[good first issue] Add Dutch locale patterns for BSN and postal codes`
**Labels:** `good first issue`, `localization`, `help wanted`
**Body:**
The pattern system supports adding new locales in 3 steps (see README → Extending with new locales). This issue is to add support for the Netherlands:
- Dutch BSN (`\d{9}`)
- Dutch postal code (`\d{4}\s?[A-Z]{2}`)
- Optional: Dutch phone number

This is a great first contribution — no changes to core logic needed.

## Issue 2: Add one more end-to-end test for streaming rehydration
**Title:** `[good first issue] Add integration test for streaming rehydration with mocked LLM`
**Labels:** `good first issue`, `tests`, `help wanted`
**Body:**
We have `secure_call_stream()` for SSE/WebSocket scenarios. Add a test in `tests_integration/` that:
1. Creates a regex-only firewall
2. Calls `secure_call_stream()` with a generator that yields tokens
3. Asserts that sensitive values are rehydrated in the final stream output

Reference existing integration tests for context structure.

## Issue 3: Improve README for first-time users
**Title:** `[good first issue] Suggest README improvements for first-time users`
**Labels:** `good first issue`, `documentation`, `help wanted`
**Body:**
If you tried to install or use pii-firewall and found the README confusing, please comment on this issue with:
- What you expected
- What happened
- What would have helped

Contributions to the README are welcome, especially around the quick-start section.

## Issue 4: Add benchmark script comparing backends
**Title:** `[help wanted] Add benchmark script to compare detection backends (latency/recall)`
**Labels:** `help wanted`, `performance`, `documentation`
**Body:**
We support regex, Presidio, GLiNER, transformers, OPF, and Nemotron backends. A small benchmark script that runs the same input through each backend and reports latency + detected entities would help users pick the right backend.

- Script path: `pii-firewall/scripts/benchmark_backends.py`
- Output: markdown table or JSON
- No dependency on heavy models required if the user selects backends manually.

## Issue 5: Dockerize the playground
**Title:** `[help wanted] Add Dockerfile for the FastAPI playground`
**Labels:** `help wanted`, `docker`, `good first issue`
**Body:**
The repo includes a FastAPI backend (`pii-firewall`) and a Next.js frontend (`pii-web-next`). Add a root-level `Dockerfile` or `compose.yml` so users can run the full playground with one command.

Acceptance criteria:
- `docker compose up` starts both backend and frontend
- Backend exposes port 8080, frontend 3010
- Uses `detector_backend=regex` by default to avoid heavy ML model downloads
