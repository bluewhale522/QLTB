import json

with open('total_devices_extracted.json', 'r', encoding='utf-8') as f:
    devs = json.load(f)

categories = {}
for d in devs:
    cat = d['category'] or 'Chưa phân loại'
    categories.setdefault(cat, []).append(d)

with open('categories_summary.txt', 'w', encoding='utf-8') as out:
    for cat, items in categories.items():
        out.write(f"\n================ NHÓM: {cat} (Số loại: {len(items)}) ================\n")
        for it in items:
            out.write(f"- {it['name']} | Model: {it['model']} | Số lượng: {it['qty_real']}\n")

print("Categories summary written.")
