import openpyxl
import json

wb = openpyxl.load_workbook('data/Thiết bị 2022.xlsx', data_only=True)

excel_structure = {}

for sheetname in wb.sheetnames:
    if not sheetname.startswith('Tầng'):
        continue
    sheet = wb[sheetname]
    rooms = []
    
    # Check rows 1 to 5 to see what is in each column
    for c in range(7, sheet.max_column + 1):
        r1 = sheet.cell(1, c).value
        r2 = sheet.cell(2, c).value
        r3 = sheet.cell(3, c).value
        r4 = sheet.cell(4, c).value
        if r4 or r3 or r2 or r1:
            rooms.append({
                'col_idx': c,
                'row1': str(r1) if r1 is not None else '',
                'row2': str(r2) if r2 is not None else '',
                'row3': str(r3) if r3 is not None else '',
                'row4': str(r4) if r4 is not None else ''
            })
    
    # Also collect all unique devices from this sheet
    devices = []
    for r in range(5, sheet.max_row + 1):
        stt = sheet.cell(r, 1).value
        cat = sheet.cell(r, 2).value
        name = sheet.cell(r, 3).value
        code = sheet.cell(r, 4).value
        spec = sheet.cell(r, 5).value
        mfg = sheet.cell(r, 6).value
        
        # Calculate how many rooms have this device and total count
        allocated_rooms = []
        for rm in rooms:
            qty = sheet.cell(r, rm['col_idx']).value
            if qty and isinstance(qty, (int, float)) and qty > 0:
                allocated_rooms.append({
                    'room': rm['row4'],
                    'qty': int(qty)
                })
        
        if name or code:
            devices.append({
                'row': r,
                'stt': stt,
                'category': str(cat).strip() if cat else '',
                'name': str(name).strip() if name else '',
                'model_code': str(code).strip() if code else '',
                'spec': str(spec).strip() if spec else '',
                'mfg': str(mfg).strip() if mfg else '',
                'allocated_rooms': allocated_rooms
            })
            
    excel_structure[sheetname] = {
        'rooms': rooms,
        'devices_count': len(devices),
        'devices': devices
    }

with open('excel_rooms_and_devices.json', 'w', encoding='utf-8') as f:
    json.dump(excel_structure, f, ensure_ascii=False, indent=2)

print("Excel analysis saved to excel_rooms_and_devices.json")
