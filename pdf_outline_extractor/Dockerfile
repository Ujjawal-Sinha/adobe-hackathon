# ========== Dockerfile ==========
# Dockerize the extractor for Linux/AMD64
FROM --platform=linux/amd64 python:3.11-slim
WORKDIR /app

# System deps for PDF parsing
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpoppler-cpp-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY extract_outline.py .

ENTRYPOINT ["python", "extract_outline.py"]