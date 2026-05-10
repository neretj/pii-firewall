# pii-firewall-clean

Clean open-source repository containing:

- `pii-firewall`: Python privacy firewall library and API
- `pii-web-next`: Next.js frontend to test anonymize -> model -> rehydrate flows

This repository contains only the reusable library and local test frontend.

## Repository Structure

```text
pii-firewall-clean/
  pii-firewall/    # Python package + FastAPI API + docs
  pii-web-next/    # Next.js test UI
```

## Prerequisites

- Python 3.10+
- Node.js 18+

## 1) Run the Backend API

```bash
cd pii-firewall
python -m pip install --upgrade pip
python -m pip install -e ".[web,presidio,langdetect]"
uvicorn privacy_firewall.web.app:create_app --factory --reload --port 8080
```

API docs: http://127.0.0.1:8080/docs

Full backend guide (HTML): [pii-firewall/docs/guide.html](pii-firewall/docs/guide.html)

Tip for VS Code: open [pii-firewall/docs/guide.html](pii-firewall/docs/guide.html) and use Open Preview (Ctrl+Shift+V).

## 2) Run the Frontend Test App

```bash
cd ../pii-web-next
copy .env.example .env.local
npm install
npm run dev
```

UI: http://127.0.0.1:3010

## 3) Use as a Dependency

For local development from this repo:

```bash
cd pii-firewall
pip install -e .
```

For published versions:

```bash
pip install pii-firewall
```

## Publish to PyPI

See [pii-firewall/PUBLISHING.md](pii-firewall/PUBLISHING.md).

## License

MIT. See [pii-firewall/LICENSE](pii-firewall/LICENSE).
