# import fitz  # PyMuPDF
# import json
# import argparse
# from collections import Counter
# import re

# # The maximum number of pages to process to adhere to the requirement.
# PAGE_LIMIT = 50

# def get_font_styles(doc):
#     """
#     Analyzes the document to find common font sizes and flags.
#     This helps in identifying the font sizes used for body text vs. headings.
#     """
#     styles = {}
#     for page_num in range(min(len(doc), PAGE_LIMIT)):
#         page = doc.load_page(page_num)
#         blocks = page.get_text("dict")["blocks"]
#         for b in blocks:
#             if "lines" in b:
#                 for l in b["lines"]:
#                     for s in l["spans"]:
#                         # Use a tuple of (size, bold_flag) as a key
#                         style_key = (round(s["size"]), "bold" in s["font"].lower())
#                         styles[style_key] = styles.get(style_key, 0) + len(s["text"].strip())
    
#     # Sort styles by character count in descending order
#     sorted_styles = sorted(styles.items(), key=lambda item: item[1], reverse=True)
#     return [style[0] for style in sorted_styles]

# def infer_headings(doc, font_styles):
#     """
#     Infers headings by assuming larger font sizes correspond to higher heading levels.
#     """
#     outline = []
#     if not font_styles:
#         return outline

#     # Assume the most common style is body text, and anything larger is a heading.
#     # We will consider up to 3 heading levels.
#     body_font_size = font_styles[0][0]
#     heading_styles = sorted([style for style in font_styles if style[0] > body_font_size], reverse=True)
    
#     # Map the top 3 largest font styles to H1, H2, H3
#     h_levels = {}
#     if len(heading_styles) > 0:
#         h_levels[heading_styles[0]] = "H1"
#     if len(heading_styles) > 1:
#         h_levels[heading_styles[1]] = "H2"
#     if len(heading_styles) > 2:
#         h_levels[heading_styles[2]] = "H3"

#     if not h_levels:
#         print("Warning: Could not identify distinct heading font sizes. Outline may be empty.")
#         return []

#     for page_num in range(min(len(doc), PAGE_LIMIT)):
#         page = doc.load_page(page_num)
#         blocks = page.get_text("dict")["blocks"]
#         for b in blocks:
#             if "lines" in b:
#                 for l in b["lines"]:
#                     if not l["spans"]:
#                         continue
                    
#                     # Consolidate text from spans in the same line
#                     line_text = "".join(s["text"] for s in l["spans"]).strip()
                    
#                     # Use the style of the first span for the whole line
#                     first_span = l["spans"][0]
#                     style_key = (round(first_span["size"]), "bold" in first_span["font"].lower())

#                     # Check if the line's style matches a heading style
#                     if style_key in h_levels and len(line_text) > 3 and not line_text.endswith('.'):
#                         # Simple check to avoid including regular sentences
#                         outline.append({
#                             "level": h_levels[style_key],
#                             "text": line_text,
#                             "page": page_num + 1
#                         })
#                         # Once a heading is found in a block, move to the next block
#                         break 
    
#     return outline


# def extract_pdf_outline(pdf_path):
#     """
#     Main function to extract title and outline from a PDF file.

#     It first tries to get the outline from the PDF's table of contents.
#     If that fails, it infers headings based on font sizes.
#     """
#     try:
#         doc = fitz.open("./file02.pdf")
#     except Exception as e:
#         print(f"Error: Could not open or read the PDF file at '{pdf_path}'.")
#         print(f"Details: {e}")
#         return None

#     # --- 1. Title Extraction ---
#     title = doc.metadata.get('title', '')
#     if not title:
#         # If no metadata title, try to find the largest text on the first page.
#         try:
#             first_page = doc.load_page(0)
#             blocks = first_page.get_text("dict")["blocks"]
#             max_font_size = 0
#             for b in blocks:
#                 if "lines" in b:
#                     for l in b["lines"]:
#                         for s in l["spans"]:
#                             if s["size"] > max_font_size:
#                                 max_font_size = s["size"]
#                                 title = s["text"]
#         except Exception:
#             # Fallback if page analysis fails
#             title = "Untitled Document"
    
#     # Clean up title
#     title = title.strip() if title else "Untitled Document"


#     # --- 2. Outline Extraction ---
#     outline = []
    
#     # Method A: Use the built-in Table of Contents (most reliable)
#     toc = doc.get_toc()
#     if toc:
#         print("Found a Table of Contents. Using it to build the outline.")
#         for level, text, page in toc:
#             if level <= 3:  # We only care about H1, H2, H3
#                 outline.append({
#                     "level": f"H{level}",
#                     "text": text.strip(),
#                     "page": page
#                 })
    
#     # Method B: Infer headings from font styles if ToC is not available
#     else:
#         print("No Table of Contents found. Inferring headings based on font styles...")
#         font_styles = get_font_styles(doc)
#         outline = infer_headings(doc, font_styles)

#     doc.close()

#     # --- 3. Final JSON structure ---
#     result = {
#         "title": title,
#         "outline": outline
#     }

#     return result

# def main():
#     """
#     Command-line interface for the script.
#     """
#     parser = argparse.ArgumentParser(
#         description="Extracts Title and Headings (H1, H2, H3) from a PDF file (up to 50 pages) and outputs a JSON file.",
#         formatter_class=argparse.RawTextHelpFormatter
#     )
#     parser.add_argument("input_pdf", help="Path to the input PDF file.")
#     parser.add_argument("output_json", help="Path to the output JSON file.")
    
#     args = parser.parse_args()

#     print(f"Processing '{args.input_pdf}'...")
#     pdf_data = extract_pdf_outline(args.input_pdf)

#     if pdf_data:
#         try:
#             with open(args.output_json, 'w', encoding='utf-8') as f:
#                 json.dump(pdf_data, f, ensure_ascii=False, indent=4)
#             print(f"Successfully created JSON outline at '{args.output_json}'")
#         except IOError as e:
#             print(f"Error: Could not write to the output file '{args.output_json}'.")
#             print(f"Details: {e}")


# if __name__ == "__main__":
#     main()







import fitz  # PyMuPDF
import json
import argparse
import re

# The maximum number of pages to process to adhere to the requirement.
PAGE_LIMIT = 50

def get_font_styles(doc):
    """
    Analyzes the document to find common font sizes and flags.
    This helps in identifying the font sizes used for body text vs. headings.
    """
    styles = {}
    for page_num in range(min(len(doc), PAGE_LIMIT)):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if "lines" in b:
                for l in b["lines"]:
                    for s in l["spans"]:
                        # Use a tuple of (size, bold_flag) as a key
                        style_key = (round(s["size"]), "bold" in s["font"].lower())
                        styles[style_key] = styles.get(style_key, 0) + len(s["text"].strip())

    # Sort styles by character count in descending order
    sorted_styles = sorted(styles.items(), key=lambda item: item[1], reverse=True)
    return [style[0] for style in sorted_styles]


def infer_headings(doc, font_styles):
    """
    Infers headings by first looking for numbered headings (e.g., "1.", "1.1")
    and then using font size for unnumbered headings.
    """
    outline = []
    if not font_styles:
        return outline

    # Assume the most common style is body text.
    body_font_style = font_styles[0]

    # Identify potential heading styles (larger or bolder than body text)
    heading_styles = sorted(
        [
            style
            for style in font_styles
            if style[0] > body_font_style[0]
               or (style[0] == body_font_style[0] and style[1] and not body_font_style[1])
        ],
        key=lambda x: x[0],
        reverse=True
    )

    # Map the top 3 unique font sizes among heading styles to H1, H2, H3
    unique_heading_sizes = sorted({size for size, _ in heading_styles}, reverse=True)
    h_level_map = {size: f"H{i+1}" for i, size in enumerate(unique_heading_sizes[:3])}

    if not h_level_map:
        print("Warning: Could not identify distinct heading font styles. Outline may be empty.")
        return []

    # Regex for numbered headings (e.g., "1.", "1.1", "1.1.1 ")
    h1_pattern = re.compile(r'^\d+\.?\s')
    h2_pattern = re.compile(r'^\d+\.\d+\.?\s')
    h3_pattern = re.compile(r'^\d+\.\d+\.\d+\.?\s')

    processed = set()

    for page_num in range(min(len(doc), PAGE_LIMIT)):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if "lines" not in b:
                continue
            for l in b["lines"]:
                if not l["spans"]:
                    continue

                line_text = "".join(s["text"] for s in l["spans"]).strip()
                if not line_text or (line_text, page_num) in processed:
                    continue

                font_size = round(l["spans"][0]["size"])
                level = None

                # 1) Numbered headings
                if h3_pattern.match(line_text):
                    level = "H3"
                elif h2_pattern.match(line_text):
                    level = "H2"
                elif h1_pattern.match(line_text):
                    level = "H1"

                # 2) Fallback to font size
                elif font_size in h_level_map:
                    # Avoid false positives: skip lines ending with a period or too long
                    if not line_text.endswith('.') and len(line_text) < 120:
                        level = h_level_map[font_size]

                if level:
                    outline.append({
                        "level": level,
                        "text": line_text,
                        "page": page_num + 1
                    })
                    processed.add((line_text, page_num))
                    break  # move to next block once we’ve got a heading

    return outline


def extract_pdf_outline(pdf_path):
    """
    Opens the PDF, extracts a title (from metadata or largest text on page 1),
    then tries the built‑in TOC or falls back to inferring H1/H2/H3 headings.
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error: Could not open PDF '{pdf_path}': {e}")
        return None

    # --- Title extraction ---
    title = doc.metadata.get('title', '').strip()
    if not title:
        # Fallback: largest text on first page
        try:
            first = doc.load_page(0)
            max_size = 0
            candidate = ""
            for b in first.get_text("dict")["blocks"]:
                if "lines" in b:
                    for l in b["lines"]:
                        for s in l["spans"]:
                            if s["size"] > max_size:
                                max_size = s["size"]
                                candidate = s["text"].strip()
            title = candidate or "Untitled Document"
        except Exception:
            title = "Untitled Document"

    # --- Outline extraction ---
    outline = []
    toc = doc.get_toc()
    if toc:
        print("Using Table of Contents...")
        for level, text, page in toc:
            if 1 <= level <= 3:
                outline.append({
                    "level": f"H{level}",
                    "text": text.strip(),
                    "page": page
                })
    else:
        print("No TOC found; inferring headings...")
        font_styles = get_font_styles(doc)
        outline = infer_headings(doc, font_styles)

    doc.close()
    return {"title": title, "outline": outline}


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Extract Title and Headings (H1, H2, H3) from a PDF (≤50 pages) "
            "and write to a JSON file."
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("input_pdf", help="Path to input PDF")
    parser.add_argument("output_json", help="Path to output JSON")
    args = parser.parse_args()

    print(f"Processing '{args.input_pdf}'...")
    data = extract_pdf_outline(args.input_pdf)
    if not data:
        return

    try:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Wrote outline to '{args.output_json}'")
    except Exception as e:
        print(f"Error writing JSON: {e}")


if __name__ == "__main__":
    main()
