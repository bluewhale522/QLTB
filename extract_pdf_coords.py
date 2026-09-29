import pypdf
import json

reader = pypdf.PdfReader('data/SƠ ĐỒ CHUẨN.pdf')

pages_data = []

def visitor_body(text, cm, tm, fontDict, fontSize):
    if text.strip():
        # tm[4] is x, tm[5] is y
        parts.append({'text': text.strip(), 'x': round(tm[4], 1), 'y': round(tm[5], 1), 'size': fontSize})

for i, page in enumerate(reader.pages):
    parts = []
    page.extract_text(visitor_text=visitor_body)
    pages_data.append({
        'page': i + 1,
        'elements': sorted(parts, key=lambda e: (-e['y'], e['x']))
    })

with open('pdf_coordinates.json', 'w', encoding='utf-8') as f:
    json.dump(pages_data, f, ensure_ascii=False, indent=2)

print("PDF coordinates extracted.")
