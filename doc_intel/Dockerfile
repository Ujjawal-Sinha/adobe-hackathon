# ========== Dockerfile ==========
FROM --platform=linux/amd64 python:3.11-slim
WORKDIR /app

# System deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY semantic_ranker.py .
ENTRYPOINT ["python", "semantic_ranker.py"]
