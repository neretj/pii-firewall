# pii-web-next

Standalone web app (Next.js + React) to test the Python `pii-firewall` API step by step.

## Requirements

- Node.js 18+
- The Python server for `pii-firewall` running at `http://127.0.0.1:8080`

## Setup

1. Copy `.env.example` to `.env.local`
2. Update `PII_API_BASE_URL` if your Python API runs on a different URL

## Development

```bash
npm install
npm run dev
```

Open: http://127.0.0.1:3010

## What it shows

- Original input
- Detected entities
- Anonymized text
- LLM backend call
- LLM response
- Rehydration
- Trace

## Integration

The app does not call Python directly from the browser; it uses internal proxy routes:

- `POST /api/run` -> proxy a `${PII_API_BASE_URL}/api/run`
- `POST /api/forget` -> proxy a `${PII_API_BASE_URL}/api/forget`
