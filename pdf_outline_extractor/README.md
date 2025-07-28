# ========== README.md ==========

# PDF Outline Extractor

## Setup

```bash
docker build -t pdf-outline-extractor:latest .
```

## Usage

```bash
docker run --rm -v $(pwd):/app pdf-outline-extractor:latest \
  --input /app/sample.pdf --output /app/outline.json
```

Or locally without Docker:

```bash
pip install -r requirements.txt
python extract_outline.py --input sample.pdf --output outline.json
```
