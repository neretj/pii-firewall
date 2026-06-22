FROM python:3.12-slim

WORKDIR /app

COPY . .

# Install web + presidio (brings spaCy) + langdetect. The pipeline primes a
# spaCy linguistic filter for every request regardless of detector_backend, so
# presidio + the en_core_web_sm model are required even for the regex default.
RUN pip install --no-cache-dir -e ".[web,presidio,langdetect]" \
    && python -m spacy download en_core_web_sm

EXPOSE 8080

# run_playground.py reads HOST/PORT from the environment.
CMD ["python", "run_playground.py"]
