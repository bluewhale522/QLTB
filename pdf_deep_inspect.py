import pypdf
import json

reader = pypdf.PdfReader('data/SƠ ĐỒ CHUẨN.pdf')
pdf_info = []

for idx, page in enumerate(reader.pages):
    page_data = {
        'page_num': idx + 1,
        'extract_text': page.extract_text(),
    }
    pdf_info.append(page_data)

with open('pdf_deep_inspect.json', 'w', encoding='utf-8') as f:
    json.dump(pdf_info, f, ensure_ascii=False, indent=2)

print("PDF deep inspection saved.")
