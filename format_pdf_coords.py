import json

with open('pdf_coordinates.json', 'r', encoding='utf-8') as f:
    pages = json.load(f)

with open('pdf_coords_summary.txt', 'w', encoding='utf-8') as out:
    for p in pages:
        out.write(f"\n================ PAGE {p['page']} ================\n")
        for el in p['elements']:
            out.write(f"({el['x']}, {el['y']}) [size={el['size']}]: {el['text']}\n")

print("Coords summary saved.")
