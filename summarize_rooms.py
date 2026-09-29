import json

with open('excel_rooms_and_devices.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('rooms_summary.txt', 'w', encoding='utf-8') as out:
    for floor, info in data.items():
        out.write(f"\n================ {floor} ================\n")
        out.write(f"Total rooms/locations: {len(info['rooms'])}\n")
        room_list = [r['row4'] for r in info['rooms'] if r['row4']]
        out.write(", ".join(room_list) + "\n")
        out.write(f"Total device types listed: {info['devices_count']}\n")

with open('pdf_deep_inspect.json', 'r', encoding='utf-8') as f:
    pdf_data = json.load(f)

with open('pdf_summary.txt', 'w', encoding='utf-8') as out:
    for p in pdf_data:
        out.write(f"\n================ PDF PAGE {p['page_num']} ================\n")
        out.write(p['extract_text'] + "\n")

print("Summaries written.")
