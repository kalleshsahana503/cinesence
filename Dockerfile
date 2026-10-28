# syntax=docker/dockerfile:1.4
# CineSense: FastAPI backend (8000) + Streamlit frontend (8501) in one container.
# Build from the project root (the folder that contains backend/ and frontend/):
#   docker build -t cinesense .
#   docker run -p 8501:8501 -p 8000:8000 -e TMDB_API_KEY=your_key cinesense

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TOKENIZERS_PARALLELISM=false \
    HF_HOME=/opt/hf-cache \
    API_URL=http://localhost:8000

# Build tools (chromadb dependencies) and curl (healthcheck)
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first so Docker caches this layer
COPY backend/requirements.txt backend/constraints.txt ./backend/
COPY frontend/requirements.txt ./frontend/
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install -r backend/requirements.txt -c backend/constraints.txt \
 && pip install -r frontend/requirements.txt

# Download the embedding model at build time so the first start is fast
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Project code
COPY backend ./backend
COPY frontend ./frontend

# Startup script: first-run ingest, optional daily auto-update, then both servers
COPY <<'EOF_START' /app/start.sh
#!/bin/sh
set -e
cd /app/backend

# Build the catalog on first start (needs TMDB_API_KEY)
if [ ! -f /app/app.db ]; then
  if [ -n "$TMDB_API_KEY" ]; then
    python ingest.py --pages "${INGEST_PAGES:-3}"
  else
    echo "TMDB_API_KEY is not set: skipping the first ingest"
  fi
fi

# Optional daily update at 4:00 AM (set ENABLE_AUTO_UPDATE=true)
if [ "$ENABLE_AUTO_UPDATE" = "true" ]; then
  python auto_update.py &
fi

uvicorn main:app --host 0.0.0.0 --port 8000 &

cd /app/frontend
exec python -m streamlit run app.py \
  --server.address 0.0.0.0 --server.port 8501 --server.headless true
EOF_START
RUN chmod +x /app/start.sh

EXPOSE 8000 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["/app/start.sh"]
