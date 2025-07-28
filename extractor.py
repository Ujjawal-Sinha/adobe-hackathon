# import pymupdf  # PyMuPDF, also known as fitz
# import json
# import re
# from collections import Counter

# class PDFOutlineExtractor:
#     """
#     Extracts a hierarchical outline (Title, H1, H2, H3) from a PDF document
#     using a multi-heuristic, two-pass classification engine.
#     """

#     def __init__(self, pdf_path):
#         """
#         Initializes the extractor with the path to the PDF file.

#         Args:
#             pdf_path (str): The file path of the PDF document.
#         """
#         try:
#             self.doc = pymupdf.open(pdf_path)
#         except Exception as e:
#             raise FileNotFoundError(f"Error opening or processing PDF file: {e}")
        
#         # Tunable parameters for the scoring model
#         self.weights = {
#             'size_ratio': 20,
#             'is_bold': 15,
#             'is_all_caps': 10,
#             'space_above_ratio': 25,
#             'has_numbering_h1': 50,
#             'has_numbering_h2': 45,
#             'has_numbering_h3': 40,
#             'is_centered': 20,
#             'word_count_penalty': -1,
#         }
#         self.thresholds = {'H1': 80, 'H2': 60, 'H3': 40}

#     def extract_outline(self):
#         """
#         Main public method to perform the full extraction and return the JSON output.

#         Returns:
#             str: A JSON formatted string containing the title and outline.
#         """
#         if not self.doc or self.doc.is_encrypted:
#             return self._to_json("Encrypted or Unreadable PDF",)

#         title = self._extract_title()
        
#         # Handle documents with no pages or that are purely images
#         if self.doc.page_count == 0:
#             return self._to_json(title,)

#         baseline_style = self._get_document_baseline()
#         if not baseline_style: # Likely an image-based PDF
#              return self._to_json(title,)

#         preliminary_headings = self._initial_classification_pass(baseline_style)
#         final_outline = self._hierarchical_refinement_pass(preliminary_headings)

#         return self._to_json(title, final_outline)

#     def _get_document_baseline(self):
#         """
#         Analyzes the document to find the most common font size and name (body text).
#         This baseline is crucial for making relative comparisons.
#         """
#         sizes = Counter()
#         fonts = Counter()
#         line_heights = []
        
#         # Analyze a sample of pages (e.g., up to the first 10 pages)
#         for page_num in range(min(self.doc.page_count, 10)):
#             page = self.doc.load_page(page_num)
#             blocks = page.get_text("dict", sort=True)["blocks"]
#             for block in blocks:
#                 if block['type'] == 0:  # Text block
#                     for line in block['lines']:
#                         line_heights.append(line['bbox'][1] - line['bbox'][2])
#                         for span in line['spans']:
#                             # Round size to handle minor floating point variations
#                             sizes[round(span['size'])] += 1
#                             fonts[span['font']] += 1
        
#         if not sizes or not fonts:
#             return None

#         baseline_size = sizes.most_common(1)
#         baseline_font = fonts.most_common(1)
#         baseline_line_height = sorted(line_heights)[len(line_heights) // 2] if line_heights else 12 # Median

#         return {
#             'size': baseline_size,
#             'font': baseline_font,
#             'line_height': baseline_line_height
#         }

#     def _extract_features_for_line(self, line, prev_block_bbox, page_width, baseline):
#         """
#         Engineers a feature vector for a given line of text.
#         """
#         if not line['spans']:
#             return None

#         # Use the first span's properties as representative for the line
#         first_span = line['spans']
#         line_text = "".join([s['text'] for s in line['spans']]).strip()
        
#         if not line_text:
#             return None

#         features = {}
        
#         # Typographical features
#         features['size_ratio'] = first_span['size'] / baseline['size']
#         # The 'flags' attribute is a bitmask. Bit 4 (16) indicates bold.
#         features['is_bold'] = (first_span['flags'] & 16) > 0
#         features['is_all_caps'] = line_text.isupper() and len(line_text) > 3

#         # Positional features
#         line_bbox = pymupdf.Rect(line['bbox'])
#         space_above = line_bbox.y0 - prev_block_bbox.y1 if prev_block_bbox else 2 * baseline['line_height']
#         features['space_above_ratio'] = space_above / baseline['line_height']
        
#         center_diff = abs(((page_width - line_bbox.width) / 2) - line_bbox.x0)
#         features['is_centered'] = center_diff < 10  # Allow 10 points tolerance for centering

#         # Syntactic features
#         word_count = len(line_text.split())
#         features['word_count'] = word_count
        
#         # Numbering features (using regex)
#         features['numbering_level'] = 0
#         # Matches patterns like "1.", "1.1.", "1.1.1."
#         num_match = re.match(r'^(\d+(\.\d+)*)\.?\s', line_text)
#         if num_match:
#             level = num_match.group(1).count('.') + 1
#             features['numbering_level'] = level
#         # Matches patterns like "Appendix A"
#         elif re.match(r'^(Appendix|Chapter|Section)\s[A-Z0-9]+', line_text, re.IGNORECASE):
#             features['numbering_level'] = 1

#         return features, line_text

#     def _initial_classification_pass(self, baseline):
#         """
#         First pass: Iterate through the document, score each line, and assign a preliminary heading level.
#         """
#         preliminary_headings = []
#         for page_num in range(self.doc.page_count):
#             page = self.doc.load_page(page_num)
#             page_width = page.rect.width
#             blocks = page.get_text("dict", sort=True)["blocks"]
#             prev_block_bbox = None

#             for block in blocks:
#                 if block['type'] == 0: # Text block
#                     for line in block['lines']:
#                         result = self._extract_features_for_line(line, prev_block_bbox, page_width, baseline)
#                         if result:
#                             features, line_text = result
#                             score = self._calculate_score(features)
                            
#                             level = None
#                             if score >= self.thresholds['H1']: level = 'H1'
#                             elif score >= self.thresholds['H2']: level = 'H2'
#                             elif score >= self.thresholds['H3']: level = 'H3'
                            
#                             if level:
#                                 preliminary_headings.append({
#                                     'level': level,
#                                     'text': line_text,
#                                     'page': page_num + 1,
#                                     'num_level': features.get('numbering_level', 0)
#                                 })
#                     prev_block_bbox = pymupdf.Rect(block['bbox'])
        
#         return preliminary_headings

#     def _calculate_score(self, features):
#         """
#         Calculates a heading score based on the weighted feature vector.
#         """
#         score = 0
        
#         # Apply weights to features
#         if features['size_ratio'] > 1.1:
#             score += (features['size_ratio'] - 1.1) * self.weights['size_ratio']
#         if features['is_bold']:
#             score += self.weights['is_bold']
#         if features['is_all_caps']:
#             score += self.weights['is_all_caps']
#         if features['space_above_ratio'] > 1.5:
#             score += self.weights['space_above_ratio']
#         if features['is_centered']:
#             score += self.weights['is_centered']
        
#         # Numbering is a very strong signal
#         if features['numbering_level'] == 1:
#             score += self.weights['has_numbering_h1']
#         elif features['numbering_level'] == 2:
#             score += self.weights['has_numbering_h2']
#         elif features['numbering_level'] >= 3:
#             score += self.weights['has_numbering_h3']
            
#         # Penalize long lines
#         if features['word_count'] > 15:
#             score += (features['word_count'] - 15) * self.weights['word_count_penalty']
            
#         return score

#     def _hierarchical_refinement_pass(self, headings):
#         """
#         Second pass: Refine the list of headings to ensure logical consistency.
#         e.g., an H3 cannot appear without a preceding H2.
#         """
#         final_outline = []
#         last_levels = {'H1': None, 'H2': None}

#         for heading in headings:
#             # Rule 1: Numbering Supremacy
#             if heading['num_level'] == 1: heading['level'] = 'H1'
#             elif heading['num_level'] == 2: heading['level'] = 'H2'
#             elif heading['num_level'] >= 3: heading['level'] = 'H3'

#             # Rule 2: Hierarchical Dependency
#             if heading['level'] == 'H1':
#                 last_levels['H1'] = heading
#                 last_levels['H2'] = None # Reset H2 context
#             elif heading['level'] == 'H2':
#                 if last_levels['H1'] is None:
#                     heading['level'] = 'H1' # Promote if no parent H1
#                     last_levels['H1'] = heading
#                 last_levels['H2'] = heading
#             elif heading['level'] == 'H3':
#                 if last_levels['H2'] is None:
#                     if last_levels['H1'] is None:
#                         heading['level'] = 'H1' # Promote to H1 if no context
#                         last_levels['H1'] = heading
#                         last_levels['H2'] = None
#                     else:
#                         heading['level'] = 'H2' # Promote to H2 if no parent H2
#                         last_levels['H2'] = heading
            
#             # Add to final outline, removing the temporary 'num_level' key
#             final_outline.append({
#                 'level': heading['level'],
#                 'text': heading['text'],
#                 'page': heading['page']
#             })
        
#         return final_outline

#     def _extract_title(self):
#         """
#         Extracts the document title using a multi-step heuristic.
#         """
#         # Step 1: Check metadata
#         if self.doc.metadata and self.doc.metadata.get('title'):
#             title = self.doc.metadata['title'].strip()
#             # Avoid generic titles
#             if title and len(title) > 3 and 'untitled' not in title.lower():
#                 return title

#         # Step 2 & 3: Typographical and Positional Analysis of the first page
#         if self.doc.page_count > 0:
#             page = self.doc.load_page(0)
#             blocks = page.get_text("dict")["blocks"]
            
#             max_font_size = 0
#             candidates = []
            
#             # Find the maximum font size on the page
#             for block in blocks:
#                 if block['type'] == 0:
#                     for line in block['lines']:
#                         for span in line['spans']:
#                             if span['size'] > max_font_size:
#                                 max_font_size = span['size']
            
#             # Collect all lines with the max font size
#             if max_font_size > 0:
#                 for block in blocks:
#                     if block['type'] == 0:
#                         for line in block['lines']:
#                             if not line['spans']: continue
#                             line_text = "".join(s['text'] for s in line['spans']).strip()
#                             if line_text and line['spans'][0]['size'] >= max_font_size - 0.5: # Tolerance
#                                 candidates.append(line_text)
            
#             if candidates:
#                 # Simple heuristic: join the first few candidates
#                 return " ".join(candidates[:2])

#         return "" # Default fallback

#     def _to_json(self, title, outline):
#         """
#         Formats the final output into the specified JSON structure.
#         """
#         return json.dumps({
#             "title": title,
#             "outline": outline
#         }, indent=4)

#     def close(self):
#         """Closes the document."""
#         self.doc.close()


import pymupdf  # PyMuPDF, also known as fitz
import json
import re
from collections import Counter

class PDFOutlineExtractor:
    """
    Extracts a hierarchical outline (Title, H1, H2, H3) from a PDF document
    using a multi-heuristic, two-pass classification engine.
    """

    def __init__(self, pdf_path):
        """
        Initializes the extractor with the path to the PDF file.

        Args:
            pdf_path (str): The file path of the PDF document.
        """
        try:
            self.doc = pymupdf.open(pdf_path)
        except Exception as e:
            raise FileNotFoundError(f"Error opening or processing PDF file: {e}")
        
        # Tunable parameters for the scoring model
        self.weights = {
            'size_ratio': 20,
            'is_bold': 15,
            'is_all_caps': 10,
            'space_above_ratio': 25,
            'has_numbering_h1': 50,
            'has_numbering_h2': 45,
            'has_numbering_h3': 40,
            'is_centered': 20,
            'word_count_penalty': -1,
        }
        self.thresholds = {'H1': 80, 'H2': 60, 'H3': 40}

    def extract_outline(self):
        """
        Main public method to perform the full extraction and return the JSON output.

        Returns:
            str: A JSON formatted string containing the title and outline.
        """
        try:
            if not self.doc or self.doc.is_encrypted:
                return self._to_json("Encrypted or Unreadable PDF", [])

            title = self._extract_title()
            if self.doc.page_count == 0:
                return self._to_json(title, [])

            baseline = self._get_document_baseline()
            if not baseline:
                return self._to_json(title, [])

            prelim = self._initial_classification_pass(baseline)
            final = self._hierarchical_refinement_pass(prelim)
            return self._to_json(title, final)
        except Exception as e:
            return self._to_json(f"Error processing {self.doc.name}", [])

    def _get_document_baseline(self):
        sizes = Counter()
        fonts = Counter()
        heights = []
        for i in range(min(self.doc.page_count, 10)):
            page = self.doc.load_page(i)
            for block in page.get_text("dict", sort=True)["blocks"]:
                if block['type'] != 0:
                    continue
                for line in block['lines']:
                    heights.append(line['bbox'][1] - line['bbox'][2])
                    for span in line['spans']:
                        sizes[round(span['size'])] += 1
                        fonts[span['font']] += 1
        if not sizes or not fonts:
            return None
        base_size = sizes.most_common(1)[0][0]
        base_height = sorted(heights)[len(heights)//2] if heights else 12
        return {'size': base_size, 'line_height': base_height}

    def _extract_features_for_line(self, line, prev_bbox, width, base):
        if not line['spans']:
            return None
        span = line['spans'][0]
        text = "".join(s['text'] for s in line['spans']).strip()
        if not text:
            return None
        features = {}
        features['size_ratio'] = span['size'] / base['size']
        features['is_bold'] = (span['flags'] & 16) > 0
        features['is_all_caps'] = text.isupper() and len(text) > 3
        bbox = pymupdf.Rect(line['bbox'])
        space = bbox.y0 - prev_bbox.y1 if prev_bbox else 2 * base['line_height']
        features['space_above_ratio'] = space / base['line_height']
        center = abs(((width - bbox.width)/2) - bbox.x0)
        features['is_centered'] = center < 10
        count = len(text.split())
        features['word_count'] = count
        features['numbering_level'] = 0
        m = re.match(r'^(\d+(?:\.\d+)*)\.?\s', text)
        if m:
            features['numbering_level'] = m.group(1).count('.') + 1
        elif re.match(r'^(Appendix|Chapter|Section)\s', text, re.I):
            features['numbering_level'] = 1
        return features, text

    def _initial_classification_pass(self, base):
        prelim = []
        for pg in range(self.doc.page_count):
            page = self.doc.load_page(pg)
            bw = page.rect.width
            prev = None
            for block in page.get_text("dict", sort=True)["blocks"]:
                if block['type'] != 0:
                    prev = pymupdf.Rect(block['bbox'])
                    continue
                for line in block['lines']:
                    res = self._extract_features_for_line(line, prev, bw, base)
                    if not res:
                        continue
                    feat, txt = res
                    sc = self._calculate_score(feat)
                    lvl = None
                    if sc >= self.thresholds['H1']:
                        lvl = 'H1'
                    elif sc >= self.thresholds['H2']:
                        lvl = 'H2'
                    elif sc >= self.thresholds['H3']:
                        lvl = 'H3'
                    if lvl:
                        prelim.append({'level': lvl, 'text': txt, 'page': pg+1, 'num_level': feat['numbering_level']})
                prev = pymupdf.Rect(block['bbox'])
        return prelim

    def _calculate_score(self, f):
        s = 0
        if f['size_ratio'] > 1.1:
            s += (f['size_ratio']-1.1)*self.weights['size_ratio']
        if f['is_bold']:
            s += self.weights['is_bold']
        if f['is_all_caps']:
            s += self.weights['is_all_caps']
        if f['space_above_ratio'] > 1.5:
            s += self.weights['space_above_ratio']
        if f['is_centered']:
            s += self.weights['is_centered']
        if f['numbering_level'] == 1:
            s += self.weights['has_numbering_h1']
        elif f['numbering_level'] == 2:
            s += self.weights['has_numbering_h2']
        elif f['numbering_level'] >= 3:
            s += self.weights['has_numbering_h3']
        if f['word_count'] > 15:
            s += (f['word_count']-15)*self.weights['word_count_penalty']
        return s

    def _hierarchical_refinement_pass(self, heads):
        final = []
        last1 = last2 = None
        for h in heads:
            lvl = h['level']
            nl = h['num_level']
            if nl == 1:
                lvl = 'H1'
            elif nl == 2:
                lvl = 'H2'
            elif nl >= 3:
                lvl = 'H3'
            if lvl == 'H1':
                last1 = h; last2 = None
            elif lvl == 'H2':
                if not last1:
                    lvl = 'H1'
                    last1 = h
                last2 = h
            elif lvl == 'H3':
                if not last2:
                    if not last1:
                        lvl = 'H1'; last1 = h
                    else:
                        lvl = 'H2'; last2 = h
            final.append({'level': lvl, 'text': h['text'], 'page': h['page']})
        return final

    def _extract_title(self):
        if self.doc.metadata.get('title'):
            t = self.doc.metadata['title'].strip()
            if len(t)>3 and 'untitled' not in t.lower():
                return t
        if self.doc.page_count:
            p = self.doc.load_page(0)
            blocks = p.get_text('dict')['blocks']
            mx = 0; cands = []
            for b in blocks:
                if b['type']!=0: continue
                for l in b['lines']:
                    for s in l['spans']:
                        mx = max(mx, s['size'])
            if mx>0:
                for b in blocks:
                    if b['type']!=0: continue
                    for l in b['lines']:
                        if not l['spans']: continue
                        txt = "".join(s['text'] for s in l['spans']).strip()
                        if txt and l['spans'][0]['size']>=mx-0.5:
                            cands.append(txt)
            if cands:
                return " ".join(cands[:2])
        return ""

    def _to_json(self, title, outline):
        return json.dumps({'title': title, 'outline': outline}, indent=4)

    def close(self):
        self.doc.close()
