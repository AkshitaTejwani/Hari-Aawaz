FROM python:3.11-slim

ENV HF_HOME=/app/hf_cache \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the multilingual embedding model at build time (avoids slow cold starts)
RUN mkdir -p /app/hf_cache && \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')" && \
    chmod -R 777 /app/hf_cache

COPY app.py .

EXPOSE 7860
CMD ["gunicorn", "-b", "0.0.0.0:7860", "--workers", "1", "--timeout", "180", "app:app"]
