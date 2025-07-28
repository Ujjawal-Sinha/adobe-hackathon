# # ========== semantic_ranker.py ==========
# """
# CLI tool for Round 1B: Given PDFs + persona + job description,
# outputs JSON with extracted_sections (using detected headings) and subsection_analysis.
# Usage:
#   python semantic_ranker.py \
#     --persona persona.json \
#     --job job.txt \
#     --out output.json \
#     docs/*.pdf
# """
# import argparse
# import json
# import os
# import glob
# import re
# from datetime import datetime
# import fitz  # PyMuPDF
# from sentence_transformers import SentenceTransformer
# import numpy as np
# from sklearn.metrics.pairwise import cosine_similarity

# PAGE_LIMIT = 50
# TOP_K = 5
# SUB_K = 5

# class OutlineExtractor:
#     def __init__(self, path):
#         self.doc = fitz.open(path)

#     def analyze_styles(self):
#         sizes = []
#         for i in range(min(len(self.doc), PAGE_LIMIT)):
#             for block in self.doc[i].get_text('dict')['blocks']:
#                 if block['type'] != 0: continue
#                 for line in block['lines']:
#                     for span in line['spans']:
#                         sizes.append(round(span['size']))
#         counts = {}
#         for s in sizes:
#             counts[s] = counts.get(s, 0) + 1
#         common = sorted(counts, key=lambda x: -counts[x])
#         return common[:2]

#     def detect_headings(self):
#         heading_sizes = self.analyze_styles()
#         pattern = re.compile(r'^(?:[0-9]+\.|[IVX]+\.)\s+')
#         headings = []
#         for i in range(min(len(self.doc), PAGE_LIMIT)):
#             for block in self.doc[i].get_text('dict')['blocks']:
#                 if block['type'] != 0: continue
#                 for line in block['lines']:
#                     for span in line['spans']:
#                         size = round(span['size'])
#                         text = span['text'].strip()
#                         if not text or len(text) < 5: continue
#                         if size in heading_sizes or pattern.match(text):
#                             headings.append({
#                                 'doc': os.path.basename(self.doc.name),
#                                 'page': i+1,
#                                 'text': text
#                             })
#         return headings

# if __name__ == '__main__':
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--persona', required=True)
#     parser.add_argument('--job', required=True)
#     parser.add_argument('--out', required=True)
#     parser.add_argument('docs', nargs='+')
#     args = parser.parse_args()

#     # Expand globs
#     pdf_paths = []
#     for pat in args.docs:
#         pdf_paths.extend(glob.glob(pat))
#     pdf_paths = sorted(set(pdf_paths))
#     if not pdf_paths:
#         print('No PDF files found.'); exit(1)

#     persona = json.load(open(args.persona, 'r', encoding='utf-8'))
#     job_desc = open(args.job, 'r', encoding='utf-8').read().strip()
#     query = persona.get('description', '') + ' ' + job_desc

#     model = SentenceTransformer('all-MiniLM-L6-v2')
#     q_emb = model.encode([query])

#     # Extract headings
#     all_headings = []
#     for pdf in pdf_paths:
#         print(f'Processing {pdf}...')
#         extractor = OutlineExtractor(pdf)
#         all_headings.extend(extractor.detect_headings())

#     if not all_headings:
#         print('No headings detected.'); exit(1)

#     texts = [h['text'] for h in all_headings]
#     embs = model.encode(texts)
#     sims = cosine_similarity(q_emb, embs)[0]

#     # Top sections
#     sec_idxs = np.argsort(-sims)[:TOP_K]
#     extracted_sections = []
#     subsections = []
#     for rank, idx in enumerate(sec_idxs, 1):
#         h = all_headings[idx]
#         extracted_sections.append({
#             'document': h['doc'],
#             'section_title': h['text'],
#             'importance_rank': rank,
#             'page_number': h['page']
#         })
#         # Split into sentences
#         parts = [s.strip()+'.' for s in h['text'].split('.') if len(s.strip()) > 20]
#         for p in parts:
#             subsections.append({'doc': h['doc'], 'page': h['page'], 'text': p})

#     # Subsection analysis only if any subsections
#     subsection_analysis = []
#     if subsections:
#         sub_texts = [s['text'] for s in subsections]
#         sub_embs = model.encode(sub_texts)
#         sub_sims = cosine_similarity(q_emb, sub_embs)[0]
#         sub_idxs = np.argsort(-sub_sims)[:SUB_K]
#         for i in sub_idxs:
#             s = subsections[i]
#             subsection_analysis.append({
#                 'document': s['doc'],
#                 'refined_text': s['text'],
#                 'page_number': s['page']
#             })

#     output = {
#         'metadata': {
#             'input_documents': [os.path.basename(p) for p in pdf_paths],
#             'persona': persona.get('description', ''),
#             'job_to_be_done': job_desc,
#             'processing_timestamp': datetime.now().isoformat()
#         },
#         'extracted_sections': extracted_sections,
#         'subsection_analysis': subsection_analysis
#     }

#     with open(args.out, 'w', encoding='utf-8') as f:
#         json.dump(output, f, indent=4, ensure_ascii=False)
#     print(f'Results written to {args.out}')




# ========== semantic_ranker.py ==========
"""
CLI tool for Round 1B: Given PDFs + persona + job description,
outputs JSON with extracted_sections and subsection_analysis.
Now extracts full paragraphs under each heading for subsections.
Usage:
  python semantic_ranker.py \
    --persona persona.json \
    --job job.txt \
    --out output.json \
    docs/*.pdf
"""
import argparse
import json
import os
import glob
import re
from datetime import datetime
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

PAGE_LIMIT = 50
TOP_K = 5
SUB_K = 5

class OutlineExtractor:
    def __init__(self, path):
        self.doc = fitz.open(path)

    def detect_headings(self):
        """Detect headings by font-size & numbering"""
        sizes = []
        for i in range(min(len(self.doc), PAGE_LIMIT)):
            for blk in self.doc[i].get_text('dict')['blocks']:
                if blk['type'] != 0: continue
                for ln in blk['lines']:
                    for sp in ln['spans']:
                        sizes.append(round(sp['size']))
        # determine top2 heading sizes
        common = sorted({s: sizes.count(s) for s in set(sizes)}.items(), key=lambda x: -x[1])
        heading_sizes = [sz for sz,_ in common[:2]]
        pattern = re.compile(r'^(?:[0-9]+\.|[IVX]+\.)\s+')
        headings = []
        for p in range(min(len(self.doc), PAGE_LIMIT)):
            page = self.doc[p]
            for blk in page.get_text('dict')['blocks']:
                if blk['type'] != 0: continue
                # capture span-level headings
                for ln in blk['lines']:
                    for sp in ln['spans']:
                        size = round(sp['size'])
                        text = sp['text'].strip()
                        if not text or len(text)<5: continue
                        if size in heading_sizes or pattern.match(text):
                            headings.append({'page':p+1,'text':text,'y':ln['bbox'][1]})
        # sort by page,y
        return sorted(headings, key=lambda x:(x['page'],x['y']))

    def extract_section_text(self, page_num, start_y, end_y=None):
        """Extract paragraph spans between start_y and end_y on page"""
        page = self.doc[page_num-1]
        lines = []
        for blk in page.get_text('dict')['blocks']:
            if blk['type']!=0: continue
            for ln in blk['lines']:
                y = ln['bbox'][1]
                if y>start_y and (end_y is None or y<end_y):
                    txt = ''.join([sp['text'] for sp in ln['spans']]).strip()
                    if txt: lines.append(txt)
        return ' '.join(lines)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--persona',required=True)
    p.add_argument('--job',required=True)
    p.add_argument('--out',required=True)
    p.add_argument('docs',nargs='+')
    args=p.parse_args()

    # expand globs
    pdfs=sorted(set(sum((glob.glob(pat) for pat in args.docs), [])))
    persona=json.load(open(args.persona,'r'))
    job_desc=open(args.job,'r').read().strip()
    query=persona.get('description','')+' '+job_desc
    model=SentenceTransformer('all-MiniLM-L6-v2')
    q_emb=model.encode([query])

    meta_docs=[]
    all_sections=[]
    for path in pdfs:
        meta_docs.append(os.path.basename(path))
        ext=OutlineExtractor(path)
        heads=ext.detect_headings()
        # determine end_y for each heading block
        for i,h in enumerate(heads):
            end_y=heads[i+1]['y'] if i+1<len(heads) and heads[i+1]['page']==h['page'] else None
            content=ext.extract_section_text(h['page'],h['y'],end_y)
            all_sections.append({
                'doc':os.path.basename(path),
                'page':h['page'],
                'title':h['text'],
                'content':content
            })
    # embed and score sections
    texts=[s['content'] for s in all_sections]
    embs=model.encode(texts)
    sims=cosine_similarity(q_emb,embs)[0]
    top_idx=np.argsort(-sims)[:TOP_K]
    extracted_sections=[]
    subsections=[]
    for rank,i in enumerate(top_idx,1):
        s=all_sections[i]
        extracted_sections.append({
            'document':s['doc'],'section_title':s['title'],
            'importance_rank':rank,'page_number':s['page']
        })
        # split content into sentences for subsections
        subs=re.split(r'(?<=[.?!])\s+',s['content'])
        for sub in subs:
            if len(sub)>30:
                subsections.append({'doc':s['doc'],'page':s['page'],'text':sub})
    # score subsections
    sub_texts=[x['text'] for x in subsections]
    sub_embs=model.encode(sub_texts) if sub_texts else np.array([])
    subsection_analysis=[]
    if sub_texts:
        sub_sims=cosine_similarity(q_emb,sub_embs)[0]
        for j in np.argsort(-sub_sims)[:SUB_K]:
            x=subsections[j]
            subsection_analysis.append({
                'document':x['doc'],'refined_text':x['text'],'page_number':x['page']
            })
    # output
    output={'metadata':{
        'input_documents':meta_docs,'persona':persona.get('description',''),
        'job_to_be_done':job_desc,'processing_timestamp':datetime.now().isoformat()
    },'extracted_sections':extracted_sections,'subsection_analysis':subsection_analysis}
    with open(args.out,'w',encoding='utf-8') as f: json.dump(output,f,indent=4,ensure_ascii=False)
    print(f'Results written to {args.out}')