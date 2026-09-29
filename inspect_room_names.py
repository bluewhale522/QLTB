import json

with open('excel_rooms_and_devices.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('room_desc.txt', 'w', encoding='utf-8') as out:
    for floor in data:
        out.write(f"\n=== {floor} ===\n")
        for r in data[floor]['rooms']:
            desc = []
            if r['row1']: desc.append(f"r1:{r['row1']}")
            if r['row2']: desc.append(f"r2:{r['row2']}")
            if r['row3']: desc.append(f"r3:{r['row3']}")
            out.write(f"Room: {r['row4']} -> {' | '.join(desc) if desc else 'none'}\n")
