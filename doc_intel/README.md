# ========== README.md ==========

# Persona‑Driven Document Intelligence (Round 1B)

## Setup

### Local

```bash
pip install -r requirements.txt
```

### Docker

```bash
docker build -t doc-intel:latest .
```

## Usage with Multiple PDFs

### Local run

```bash
python semantic_ranker.py \
  --persona persona.json \
  --job job.txt \
  --out ranking.json \
  doc1.pdf doc2.pdf doc3.pdf
```

Or using a shell glob:

```bash
python semantic_ranker.py --persona persona.json --job job.txt --out ranking.json docs/*.pdf
```

### Docker run

```bash
docker run --rm -v $(pwd):/app doc-intel:latest \
  --persona /app/persona.json \
  --job /app/job.txt \
  --out /app/ranking.json \
  /app/docs/*.pdf
```

The script will produce **`ranking.json`** containing the top 10 most relevant text sections across all input PDFs, ranked by semantic similarity to your persona and job description.
