import fitz
import json
import re
import argparse
import os
from concurrent.futures import ProcessPoolExecutor
from collections import Counter

PAGE_LIMIT = 50  # limit pages to scan for performance
NUMERIC_PATTERN = re.compile(r'^([0-9]+(?:\.[0-9]+)*)\s+')

class OutlineExtractor:
    def __init__(self, path):
        self.path = path
        self.doc = fitz.open(path)
        self.spans = []

    def collect_spans(self):
        """Collect text spans with size, flags, bbox, page info."""
        for pno in range(min(len(self.doc), PAGE_LIMIT)):
            page = self.doc[pno]
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue
                        self.spans.append({
                            'text': text,
                            'size': span.get('size', 0),
                            'flags': span.get('flags', 0),  # bold/italic bits
                            'bbox': span.get('bbox', []),  # [x0, y0, x1, y1]
                            'page': pno + 1
                        })

    def detect_body_size(self):
        """Determine the most common font size as body text size."""
        sizes = [round(s['size'],1) for s in self.spans]
        if not sizes:
            return None
        freq = Counter(sizes)
        return freq.most_common(1)[0][0]

    def extract_title(self):
        """Get title from metadata or fallback to largest span on page 1."""
        title = self.doc.metadata.get('title', '').strip()
        if title:
            return title
        # fallback: largest-sized span on first page, topmost
        p1 = [s for s in self.spans if s['page'] == 1]
        if not p1:
            return ''
        # sort by size desc, then y0 asc
        p1_sorted = sorted(p1, key=lambda s: (-s['size'], s['bbox'][1]))
        return p1_sorted[0]['text']

    def assign_level(self, span, body_size):
        text = span['text']
        size = span['size']
        flags = span['flags']

        # 1) Numeric hierarchy
        m = NUMERIC_PATTERN.match(text)
        if m:
            depth = m.group(1).count('.') + 1
            return f'H{min(depth, 4)}'

        # 2) All-caps headings
        if text.isupper() and size >= body_size + 1:
            return 'H1'

        # 3) Bold text slightly larger than body
        BOLD_FLAG = 2  # bit 1 indicates bold
        if (flags & BOLD_FLAG) and size >= body_size + 0.5:
            return 'H2'

        # 4) Larger size than body as H2
        if size >= body_size + 2:
            return 'H2'

        return None

    def detect_headings(self):
        """Apply heuristics to classify spans as headings."""
        self.collect_spans()
        body_size = self.detect_body_size() or 0
        headings = []
        for span in self.spans:
            level = self.assign_level(span, body_size)
            if level:
                headings.append({
                    'level': level,
                    'text': span['text'],
                    'page': span['page']
                })

        if len(headings) == 1 and len(self.doc) == 1:
            headings[0]['page'] = 0
        return headings

    def build_outline(self):
        title = self.extract_title()
        outline = self.detect_headings()
        return {'title': title, 'outline': outline}


def process_file(input_path, output_path):
    try:
        extractor = OutlineExtractor(input_path)
        result = extractor.build_outline()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Processed {os.path.basename(input_path)}")
    except Exception as e:
        print(f"Error {input_path}: {e}")


def main():
    parser = argparse.ArgumentParser(description='Batch PDF outline extractor')
    parser.add_argument('--input_dir',
                        default=os.environ.get('INPUT_DIR', '/app/input'),
                        help='Directory of PDF files (default /app/input)')
    parser.add_argument('--output_dir',
                        default=os.environ.get('OUTPUT_DIR', '/app/output'),
                        help='Directory for JSON outputs (default /app/output)')
    parser.add_argument('--workers', type=int, default=4, help='Parallel workers')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    pdfs = [f for f in os.listdir(args.input_dir) if f.lower().endswith('.pdf')]
    tasks = []
    for pdf in pdfs:
        in_path = os.path.join(args.input_dir, pdf)
        base = os.path.splitext(pdf)[0]
        out_path = os.path.join(args.output_dir, f"{base}.json")
        tasks.append((in_path, out_path))

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        for inp, out in tasks:
            executor.submit(process_file, inp, out)

    print('Batch processing complete.')

if __name__ == '__main__':
    main()

# Expected Execution  We will build the docker image using the following command: ```docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier``` After building the image, we will run the solution using the run command specified in the submitted instructions. ```docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output -network none mysolutionname:somerandomidentifier```  


# to build the docker image, you can use the following command;
# ```docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .```

# to run the script with docker as in expected execution, you can use the following command;
# ```docker run --rm -v ${PWD}\input:/app/input -v ${PWD}\output:/app/output --network none  mysolutionname:somerandomidentifier```

