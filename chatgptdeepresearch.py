# import fitz  # PyMuPDF
# import re
# import json

# def extract_title_and_headings(pdf_path):
#     doc = fitz.open(pdf_path)
#     title = ""
#     outline = []

#     # === Title Extraction (page 1) ===
#     if doc.page_count > 0:
#         page0 = doc.load_page(0)
#         blocks = page0.get_text("dict")["blocks"]
#         # Collect all text spans on page 1
#         spans = [span for b in blocks if b['type']==0 
#                  for line in b["lines"] for span in line["spans"]]
#         if spans:
#             # Find the maximum font size on page 1
#             max_size = max(span["size"] for span in spans)
#             page_height = page0.rect.height
#             # Candidate spans with that max size
#             top_spans = [s for s in spans if s["size"] == max_size]
#             if top_spans:
#                 top_y = min(s["bbox"][1] for s in top_spans)
#                 # If these spans are too low (e.g. bottom-of-page decoration), skip them
#                 if top_y > 0.8 * page_height:
#                     # Try next-largest font instead
#                     sizes = sorted({s["size"] for s in spans}, reverse=True)
#                     for sz in sizes:
#                         if sz < max_size:
#                             candidate = [s for s in spans if s["size"] == sz]
#                             if candidate and min(s["bbox"][1] for s in candidate) <= 0.8*page_height:
#                                 top_spans = candidate
#                                 break
#                 # Combine the remaining top spans into the title (sorted by position)
#                 top_spans.sort(key=lambda s: (s["bbox"][1], s["bbox"][0]))
#                 title = " ".join(s["text"].strip() for s in top_spans).strip()
#             # Fallback: first non-empty line if no clear title found
#             if not title or re.match(r'^\d+\s*$', title):
#                 for b in blocks:
#                     if b['type'] != 0: 
#                         continue
#                     for line in b["lines"]:
#                         line_text = "".join(span["text"] for span in line["spans"]).strip()
#                         # Skip trivial labels
#                         if not line_text or line_text.endswith(":") and len(line_text.split())<=2:
#                             continue
#                         title = line_text
#                         break
#                     if title:
#                         break

#     # === Heading Extraction (all pages) ===
#     prev_levels = []
#     for page_num in range(doc.page_count):
#         page = doc.load_page(page_num)
#         blocks = page.get_text("dict")["blocks"]
#         for b in blocks:
#             if b['type'] != 0:  # skip non-text blocks
#                 continue
#             block_text = "".join(span["text"] for line in b["lines"] 
#                                  for span in line["spans"]).strip()
#             if not block_text:
#                 continue
#             # Skip common footer/header or TOC artifacts (e.g. "... 5")
#             if re.match(r'^\.*\s*\d+$', block_text) or block_text.lower().startswith("page "):
#                 continue

#             level = None
#             heading_text = None

#             # (1) Numeric prefix (e.g. "1.", "2.1", etc.)
#             m = re.match(r'^(\d+(?:\.\d+)*)[.\)]\s*(.+)$', block_text)
#             if m:
#                 # Skip numeric if it’s small text (likely list, not a section heading)
#                 size0 = b["lines"][0]["spans"][0]["size"]
#                 if size0 > 11:  # threshold can be adjusted
#                     sec = m.group(1)
#                     text_after = m.group(2).strip()
#                     dots = sec.count('.')
#                     level = min(dots+1, 4)
#                     heading_text = text_after
#             else:
#                 # (2) Appendix (treat as H1)
#                 m2 = re.match(r'^(Appendix)\s+([A-Z\d])[:,]?\s*(.*)$', block_text, re.IGNORECASE)
#                 if m2:
#                     level = 1
#                     heading_text = block_text
#                 else:
#                     # (3) Style-based: bold or large font
#                     span0 = b["lines"][0]["spans"][0]
#                     if ("Bold" in span0["font"] or span0["size"] > 12):
#                         heading_text = block_text
#                         x0 = span0["bbox"][0]
#                         # Indentation hint
#                         level = 1 if x0 < page.rect.width * 0.1 else 2

#             if level:
#                 # Clamp level to H1–H4
#                 level = max(1, min(4, level))
#                 # Enforce hierarchy: skip if jumping too far
#                 if prev_levels and level > prev_levels[-1] + 1:
#                     continue
#                 prev_levels = prev_levels[:level-1] + [level]
#                 outline.append({"level": f"H{level}", 
#                                 "text": heading_text, 
#                                 "page": page_num+1})

#     return {"title": title, "outline": outline}

# # Example usage (command-line):
# if __name__ == "__main__":
#     import sys
#     pdf_file = sys.argv[1]  # path to PDF
#     result = extract_title_and_headings(pdf_file)
#     print(json.dumps(result, indent=2))




# version 2.0

# import fitz  # PyMuPDF
# import json
# import re
# import sys
# from collections import defaultdict

# PAGE_LIMIT = 50

# # Heuristics for heading detection
# heading_patterns = [
#     (r"^\d+\.\d+\.\d+\.\d+\s+.*", "H4"),
#     (r"^\d+\.\d+\.\d+\s+.*", "H3"),
#     (r"^\d+\.\d+\s+.*", "H2"),
#     (r"^\d+\.\s+.*", "H1"),
#     (r"^Appendix [A-Z]+.*", "H2"),
#     (r"^(Table of Contents|Revision History|Acknowledgements|Introduction|Overview).*", "H1"),
# ]

# noise_patterns = [
#     r"^\.*$",
#     r"^[-_.]{5,}$",
#     r"^\d+\.$",
#     r"^[A-Z\s\d\-:]{10,}$",
#     r"http[s]?://",
#     r"^WWW\.",
#     r"^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$"
# ]

# def is_noise(text):
#     for pat in noise_patterns:
#         if re.fullmatch(pat, text.strip()):
#             return True
#     return False

# def classify_heading(text):
#     for pattern, level in heading_patterns:
#         if re.match(pattern, text.strip(), re.IGNORECASE):
#             return level
#     return None

# def extract_title(page):
#     blocks = page.get_text("dict")["blocks"]
#     best_block = None
#     best_size = 0

#     for b in blocks:
#         for l in b.get("lines", []):
#             for s in l.get("spans", []):
#                 if len(s["text"].strip()) > 5 and s["size"] > best_size:
#                     best_size = s["size"]
#                     best_block = s["text"].strip()

#     return best_block if best_block else "----------------"

# def process_pdf(filepath):
#     doc = fitz.open(filepath)
#     max_pages = min(len(doc), PAGE_LIMIT)

#     # Extract title from first page
#     title = extract_title(doc[0]).strip()

#     headings = []
#     last_levels = {"H1": False, "H2": False, "H3": False, "H4": False}

#     for i in range(max_pages):
#         page = doc[i]
#         blocks = page.get_text("dict")["blocks"]
#         for b in blocks:
#             for l in b.get("lines", []):
#                 for s in l.get("spans", []):
#                     text = s["text"].strip()
#                     if not text or is_noise(text):
#                         continue

#                     level = classify_heading(text)
#                     if not level:
#                         continue

#                     # Enforce hierarchy: e.g., H2 only appears after H1
#                     if level == "H2" and not last_levels["H1"]:
#                         continue
#                     if level == "H3" and not last_levels["H2"]:
#                         continue
#                     if level == "H4" and not last_levels["H3"]:
#                         continue

#                     # Mark this level as seen
#                     last_levels[level] = True
#                     heading = {
#                         "level": level,
#                         "text": text + " ",
#                         "page": i
#                     }
#                     headings.append(heading)

#     result = {
#         "title": title + " ",
#         "outline": headings
#     }
#     return result


# if __name__ == "__main__":
#     if len(sys.argv) != 2:
#         print("Usage: python chatgptdeepresearch.py <pdf_file>")
#         sys.exit(1)

#     filepath = sys.argv[1]
#     result = process_pdf(filepath)
#     print(json.dumps(result, indent=2, ensure_ascii=False))




# version 3
import fitz  # PyMuPDF
import re
import json
import sys

# Maximum pages to process
PAGE_LIMIT = 50

class PDFOutlineExtractor:
    """
    Extracts document title and hierarchical headings (H1-H4) from a PDF.
    """
    def __init__(self, pdf_path):
        self.doc = fitz.open(pdf_path)
        self.max_pages = min(len(self.doc), PAGE_LIMIT)
        # Patterns and thresholds
        self.noise_patterns = [
            r"^\.*$", r"^[\-_.]{5,}$", r"^\d+\.$",
            r"http[s]?://", r"^WWW\."
        ]
        self.heading_regex = [
            (re.compile(r"^(?P<num>\d+(?:\.\d+){3})[\.\)]?\s+(?P<txt>.+)$"), "H4"),
            (re.compile(r"^(?P<num>\d+(?:\.\d+){2})[\.\)]?\s+(?P<txt>.+)$"), "H3"),
            (re.compile(r"^(?P<num>\d+\.\d+)[\.\)]?\s+(?P<txt>.+)$"), "H2"),
            (re.compile(r"^(?P<num>\d+)[\.\)]?\s+(?P<txt>.+)$"), "H1"),
            (re.compile(r"^(Appendix)\s+(?P<txt>.+)", re.IGNORECASE), "H1"),
        ]

    def is_noise(self, text: str) -> bool:
        for pat in self.noise_patterns:
            if re.fullmatch(pat, text.strip()):
                return True
        return False

    def extract_title(self) -> str:
        """Pick the most prominent text on page 1 as title"""
        page = self.doc[0]
        blocks = page.get_text("dict")["blocks"]
        best = (0, "")  # (font size, text)
        for b in blocks:
            if b['type'] != 0: continue
            for line in b['lines']:
                for span in line['spans']:
                    txt = span['text'].strip()
                    size = span['size']
                    # longer than small labels
                    if len(txt) > 3 and size > best[0]:
                        best = (size, txt)
        return best[1] if best[1] else ''

    def classify_heading(self, text: str) -> str:
        """Return level H1-H4 or '' if not a heading"""
        for rex, level in self.heading_regex:
            m = rex.match(text)
            if m:
                # get clean text
                txt = m.groupdict().get('txt', text).strip()
                return level, txt
        return '', ''

    def extract_outline(self) -> dict:
        title = self.extract_title()
        outline = []
        # track last seen level for hierarchy
        last_level_index = 0
        levels = ['H1', 'H2', 'H3', 'H4']

        for pno in range(self.max_pages):
            page = self.doc[pno]
            blocks = page.get_text("dict")["blocks"]
            for b in blocks:
                if b['type'] != 0: continue
                text = ''.join(span['text'] for line in b['lines'] for span in line['spans']).strip()
                if not text or self.is_noise(text):
                    continue
                level, clean = self.classify_heading(text)
                if not level:
                    continue
                idx = levels.index(level)
                # enforce hierarchy jump <= 1
                if idx > last_level_index + 1:
                    continue
                last_level_index = idx
                outline.append({
                    "level": level,
                    "text": clean,
                    "page": pno + 1
                })
        return {"title": title, "outline": outline}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extractor.py <pdf_file>")
        sys.exit(1)
    extractor = PDFOutlineExtractor(sys.argv[1])
    result = extractor.extract_outline()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    