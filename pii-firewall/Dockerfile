FROM python:3.12-slim

WORKDIR /app

COPY . .

# Install the "web" extra only (FastAPI + uvicorn). This is the regex-only,
# no-ML install: it deliberately leaves out the presidio/transformers/gliner
# extras so the image stays small and needs no model downloads. The default
# detector_backend is "regex", which requires nothing beyond the base package.
RUN pip install --no-cache-dir -e ".[web]"

EXPOSE 8080

# run_playground.py reads HOST/PORT from the environment.
CMD ["python", "run_playground.py"]
