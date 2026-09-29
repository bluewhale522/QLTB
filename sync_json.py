import os
import json
import re
import sqlite3
import unicodedata

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def safe_print(msg):
    try:
        print(msg)
    except Exception:
        try:
            print(str(msg).encode('ascii', 'backslashreplace').decode('ascii'))
        except Exception:
            pass

def normalize_text(text):
    if not text:
        return ''
    return unicodedata.normalize('NFC', str(text)).strip()

def get_floor_and_room(loc_name):
    floor = 'Tầng 1'
    room_code = ''
    if not loc_name:
        return floor, room_code

    loc_str = normalize_text(loc_name)

    # 1. Tra cứu trực tiếp từ bảng locations trong SQLite nếu có
    try:
        db_path = os.path.join(BASE_DIR, 'school_equipment.db')
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT floor, code FROM locations WHERE name = ? OR code = ? LIMIT 1", (loc_str, loc_str))
            row = cur.fetchone()
            conn.close()
            if row:
                return normalize_text(row[0]), normalize_text(row[1])
    except Exception as e:
        safe_print(f"[SYNC_JSON] Error reading DB location: {e}")

    # 2. Dự phòng bằng Regex nếu không truy vấn được DB
    m = re.search(r'([1-6])F', loc_str, re.IGNORECASE)
    if m:
        floor = f"Tầng {m.group(1)}"
    else:
        for f in ['Tầng 1', 'Tầng 2', 'Tầng 3', 'Tầng 4', 'Tầng 5', 'Tầng 6']:
            if f.lower() in loc_str.lower():
                floor = f
                break

    if ' - ' in loc_str:
        room_code = loc_str.split(' - ')[0].strip()
    else:
        room_code = loc_str

    return floor, room_code

def sync_add_device_to_json(device_data):
    """
    Tự động cập nhật thiết bị mới thêm vào:
    1. total_devices_extracted.json (Danh sách chuẩn thiết bị)
    2. excel_rooms_and_devices.json (Danh sách bố trí phòng và thiết bị)
    """
    try:
        name = normalize_text(device_data.get('name', ''))
        category = normalize_text(device_data.get('category', ''))
        code = normalize_text(device_data.get('code', ''))
        location = normalize_text(device_data.get('current_location', ''))
        spec = normalize_text(device_data.get('specification', ''))
        supplier = normalize_text(device_data.get('supplier', ''))
        floor, room_code = get_floor_and_room(location)

        # 1. Cập nhật total_devices_extracted.json
        std_path = os.path.join(BASE_DIR, 'total_devices_extracted.json')
        if os.path.exists(std_path):
            with open(std_path, 'r', encoding='utf-8') as f:
                std_list = json.load(f)

            found_item = None
            for d in std_list:
                if normalize_text(d.get('name', '')).lower() == name.lower():
                    found_item = d
                    break

            if found_item:
                found_item['qty_in'] = found_item.get('qty_in', 0) + 1
                found_item['qty_real'] = found_item.get('qty_real', 0) + 1
            else:
                new_item = {
                    'stt': len(std_list) + 1,
                    'category': category,
                    'name': name,
                    'model': code,
                    'spec': spec,
                    'mfg': supplier,
                    'qty_in': 1,
                    'qty_real': 1
                }
                std_list.append(new_item)

            with open(std_path, 'w', encoding='utf-8') as f:
                json.dump(std_list, f, ensure_ascii=False, indent=2)

        # 2. Cập nhật excel_rooms_and_devices.json
        excel_json_path = os.path.join(BASE_DIR, 'excel_rooms_and_devices.json')
        if os.path.exists(excel_json_path):
            with open(excel_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Đảm bảo tầng tồn tại
            if floor not in data:
                data[floor] = {'rooms': [], 'devices_count': 0, 'devices': []}

            floor_data = data[floor]
            devices = floor_data.setdefault('devices', [])

            # Tìm xem thiết bị đã có trong danh mục tầng này chưa
            found_dev = None
            for d in devices:
                if normalize_text(d.get('name', '')).lower() == name.lower() or (code and normalize_text(d.get('model_code', '')).lower() == code.lower()):
                    found_dev = d
                    break

            if found_dev:
                alloc = found_dev.setdefault('allocated_rooms', [])
                room_entry = next((r for r in alloc if normalize_text(r.get('room', '')) == room_code), None)
                if room_entry:
                    room_entry['qty'] = room_entry.get('qty', 0) + 1
                else:
                    if room_code:
                        alloc.append({'room': room_code, 'qty': 1})
            else:
                new_dev = {
                    'row': len(devices) + 1,
                    'stt': len(devices) + 1,
                    'category': category,
                    'name': name,
                    'model_code': code,
                    'spec': spec,
                    'mfg': supplier,
                    'allocated_rooms': [{'room': room_code, 'qty': 1}] if room_code else []
                }
                devices.append(new_dev)
                floor_data['devices_count'] = len(devices)

            with open(excel_json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        safe_print(f"[SYNC_JSON] Successfully synced added device: {code} - {name} ({location})")
        return True
    except Exception as e:
        safe_print(f"[SYNC_JSON] Error syncing added device: {e}")
        return False

def sync_move_device_in_json(device_code, device_name, from_location, to_location):
    """
    Tự động cập nhật khi di chuyển thiết bị trong excel_rooms_and_devices.json
    """
    try:
        from_floor, from_room = get_floor_and_room(from_location)
        to_floor, to_room = get_floor_and_room(to_location)
        dev_code = normalize_text(device_code)
        dev_name = normalize_text(device_name)

        excel_json_path = os.path.join(BASE_DIR, 'excel_rooms_and_devices.json')
        if not os.path.exists(excel_json_path):
            return False

        with open(excel_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 1. Giảm số lượng ở phòng cũ (tầng cũ)
        if from_floor in data:
            for d in data[from_floor].get('devices', []):
                d_name = normalize_text(d.get('name', ''))
                d_code = normalize_text(d.get('model_code', ''))
                if (dev_name and d_name.lower() == dev_name.lower()) or (dev_code and d_code.lower() == dev_code.lower()):
                    alloc = d.get('allocated_rooms', [])
                    for r in alloc:
                        if normalize_text(r.get('room', '')) == from_room:
                            r['qty'] = max(0, r.get('qty', 1) - 1)
                    d['allocated_rooms'] = [r for r in alloc if r.get('qty', 0) > 0]
                    break

        # 2. Tăng số lượng ở phòng mới (tầng mới)
        if to_floor not in data:
            data[to_floor] = {'rooms': [], 'devices_count': 0, 'devices': []}

        floor_data = data[to_floor]
        devices = floor_data.setdefault('devices', [])

        found_dev = None
        for d in devices:
            d_name = normalize_text(d.get('name', ''))
            d_code = normalize_text(d.get('model_code', ''))
            if (dev_name and d_name.lower() == dev_name.lower()) or (dev_code and d_code.lower() == dev_code.lower()):
                found_dev = d
                break

        if found_dev:
            alloc = found_dev.setdefault('allocated_rooms', [])
            room_entry = next((r for r in alloc if normalize_text(r.get('room', '')) == to_room), None)
            if room_entry:
                room_entry['qty'] = room_entry.get('qty', 0) + 1
            else:
                if to_room:
                    alloc.append({'room': to_room, 'qty': 1})
        else:
            new_dev = {
                'row': len(devices) + 1,
                'stt': len(devices) + 1,
                'category': 'Thiết bị di chuyển',
                'name': dev_name,
                'model_code': dev_code,
                'spec': '',
                'mfg': '',
                'allocated_rooms': [{'room': to_room, 'qty': 1}] if to_room else []
            }
            devices.append(new_dev)
            floor_data['devices_count'] = len(devices)

        with open(excel_json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        safe_print(f"[SYNC_JSON] Successfully synced moved device: {dev_code} ({from_location} -> {to_location})")
        return True
    except Exception as e:
        safe_print(f"[SYNC_JSON] Error syncing moved device: {e}")
        return False
