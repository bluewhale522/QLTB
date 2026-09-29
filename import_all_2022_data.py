import openpyxl
import sqlite3
import json
import os
from datetime import datetime
from database import DB_PATH, get_db

def import_users_from_excel(cursor):
    """
    Import toàn bộ cán bộ, giáo viên, nhân viên từ file:
    data/SIGMA_EMAIL & CONTACT 2026.xlsx - Sheet DATA
    """
    excel_path = 'data/SIGMA_EMAIL & CONTACT 2026.xlsx'
    if not os.path.exists(excel_path):
        print(f"Warning: {excel_path} not found. Skipping user import.")
        return

    wb = openpyxl.load_workbook(excel_path, data_only=True)
    if 'DATA' not in wb.sheetnames:
        print("Warning: Sheet 'DATA' not found in contact file.")
        return

    ws = wb['DATA']
    cursor.execute("DELETE FROM users")

    seen_codes = set()
    user_records = []
    auto_code_idx = 1

    for r in range(2, ws.max_row + 1):
        status = str(ws.cell(r, 2).value or '').strip()
        khoi = str(ws.cell(r, 3).value or '').strip()
        dept = str(ws.cell(r, 4).value or '').strip()
        manv = str(ws.cell(r, 5).value or '').strip()
        name = str(ws.cell(r, 6).value or '').strip()
        title = str(ws.cell(r, 10).value or '').strip()
        email = str(ws.cell(r, 12).value or '').strip()
        phone_val = ws.cell(r, 13).value

        if not name:
            continue

        # Chuẩn hóa số điện thoại: thêm số 0 đầu nếu thiếu, lọc chỉ lấy số
        phone = ""
        if phone_val is not None:
            raw_phone = str(phone_val).strip()
            if '.' in raw_phone:
                raw_phone = raw_phone.split('.')[0]
            raw_phone = ''.join(ch for ch in raw_phone if ch.isdigit())
            if len(raw_phone) == 9:
                phone = "0" + raw_phone
            elif len(raw_phone) >= 10:
                phone = raw_phone if raw_phone.startswith('0') else ("0" + raw_phone)
            else:
                phone = raw_phone

        # Chuẩn hóa phòng ban / cấp học
        final_dept = dept
        if not final_dept:
            if khoi:
                final_dept = "Ban Lãnh đạo (STH)" if khoi == "STH" else (f"Khối {khoi}" if not khoi.startswith("Khối") else khoi)
            else:
                final_dept = "Cán bộ trường"

        # Đảm bảo mã nhân viên duy nhất
        code = manv
        if not code:
            code = f"SIGMA-{auto_code_idx:03d}"
            auto_code_idx += 1

        base_code = code
        dup_count = 1
        while code in seen_codes:
            dup_count += 1
            code = f"{base_code}-{dup_count}"
        seen_codes.add(code)

        # Phân loại vai trò
        role = "teacher"
        t_lower = title.lower()
        if any(w in t_lower for w in ['chủ tịch', 'tổng giám đốc', 'thành viên hđqt', 'trưởng ban', 'phó ban', 'kế toán trưởng', 'hiệu trưởng', 'phó hiệu trưởng', 'quản trị']):
            role = "admin"
        elif any(w in t_lower for w in ['kỹ thuật', 'cntt', 'it', 'thiết bị']):
            role = "technician"

        user_records.append((code, name, email, phone, role, final_dept))

    cursor.executemany("""
        INSERT INTO users (code, fullname, email, phone, role, department)
        VALUES (?, ?, ?, ?, ?, ?)
    """, user_records)
    print(f"Imported {len(user_records)} staff/users from SIGMA_EMAIL & CONTACT 2026.xlsx (Sheet DATA).")


def run_import():
    conn = get_db()
    cursor = conn.cursor()

    # 1. Update database schema
    cursor.execute("PRAGMA table_info(locations)")
    cols = [r['name'] for r in cursor.fetchall()]
    if 'floor' not in cols:
        cursor.execute("ALTER TABLE locations ADD COLUMN floor TEXT DEFAULT 'Tầng 1'")

    cursor.execute("PRAGMA table_info(devices)")
    dev_cols = [r['name'] for r in cursor.fetchall()]
    if 'assigned_user' not in dev_cols:
        cursor.execute("ALTER TABLE devices ADD COLUMN assigned_user TEXT")
    conn.commit()

    # 2. Import Users from SIGMA_EMAIL & CONTACT 2026.xlsx
    import_users_from_excel(cursor)
    conn.commit()

    # 3. Load mapped rooms
    with open('all_rooms_mapped.json', 'r', encoding='utf-8') as f:
        all_rooms = json.load(f)

    # Insert / Replace locations
    cursor.execute("DELETE FROM locations")
    for r in all_rooms:
        cursor.execute("""
            INSERT INTO locations (code, name, type, floor, manager_name, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (r['code'], r['name'], r['type'], r['floor'], 'Ban Quản trị Cơ sở vật chất', f"Vị trí {r['code']} thuộc {r['floor']}"))
    conn.commit()
    print(f"Inserted {len(all_rooms)} locations with floor groupings.")

    # 4. Update Categories
    categories = [
        ("Màn hình máy tính", "tv"),
        ("Máy tính bàn", "monitor"),
        ("Thiết bị mạng & Router", "network"),
        ("Unifi & Wifi mạng", "wifi"),
        ("Laptop giảng dạy", "laptop"),
        ("Máy in & Photocopy", "printer"),
        ("Máy chiếu & Phông chiếu", "projector"),
        ("Camera & An ninh", "video"),
        ("Âm thanh & Trợ giảng", "volume-2"),
        ("Máy chấm công & Thẻ", "fingerprint"),
        ("Server & Máy chủ", "server"),
        ("Máy đặt suất ăn", "utensils"),
        ("Dụng cụ Thí nghiệm", "flask-conical"),
        ("Dụng cụ Thể thao", "trophy"),
        ("Khác", "package")
    ]
    cursor.execute("DELETE FROM categories")
    cursor.executemany("INSERT INTO categories (name, icon) VALUES (?, ?)", categories)
    conn.commit()

    # 5. Phân loại thiết bị và sinh mã theo đúng quy chuẩn:
    # Sigma-PC-001 (Case máy tính), Sigma-M-001 (Màn hình), Sigma-ROUTER-001 (Router / Mạng), etc.
    # Đánh số bắt đầu tuần tự từ Tầng 1 đến Tầng 6
    def categorize_device(raw_cat, name):
        rc = str(raw_cat or '').strip().lower()
        nm = str(name or '').strip().lower()

        # 1. Màn hình
        if 'màn hình' in nm or 'màn hình' in nm or 'màn hình' in rc:
            return 'Màn hình máy tính', 'M'
        # 2. Laptop
        if 'laptop' in rc or 'laptop' in nm:
            return 'Laptop giảng dạy', 'LT'
        # 3. Máy in
        if 'in' in rc or 'photo' in rc or 'máy in' in nm:
            return 'Máy in & Photocopy', 'PRN'
        # 4. Máy chiếu
        if 'chiếu' in rc or 'chiếu' in nm:
            return 'Máy chiếu & Phông chiếu', 'MC'
        # 5. Wifi
        if 'unifi' in rc or 'wifi' in rc or 'phát sóng không dây' in nm:
            return 'Unifi & Wifi mạng', 'WF'
        # 6. Thiết bị mạng / Router / Switch
        if any(w in nm for w in ['switch', 'router', 'firewall', 'cân bằng tải', 'tường lửa', 'slot mở rộng', 'cáp stack', 'module quang', 'module đồng']) or 'mạng' in rc:
            return 'Thiết bị mạng & Router', 'ROUTER'
        # 7. Server / Máy chủ
        if 'server' in rc or 'máy chủ' in rc or 'server' in nm or 'máy chủ' in nm or 'workstation' in nm:
            return 'Server & Máy chủ', 'SRV'
        # 8. Máy chấm công & Thẻ
        if 'chấm công' in rc or 'quẹt thẻ' in rc or 'chấm công' in nm or 'quẹt thẻ' in nm:
            return 'Máy chấm công & Thẻ', 'CC'
        # 9. Camera & An ninh
        if 'camera' in rc or 'camera' in nm or 'đầu lưu trữ' in nm or 'đầu lưu trữ' in nm or 'smart-ups' in nm:
            return 'Camera & An ninh', 'CAM'
        # 10. Âm thanh & Trợ giảng
        if 'âm thanh' in rc or any(w in nm for w in ['loa ', 'loa hộp', 'loa phóng', 'mic ', 'micro', 'âm ly', 'mixer', 'bàn trộn']):
            return 'Âm thanh & Trợ giảng', 'AT'
        # 11. Máy tính bàn / Case máy
        if 'máy tính bàn' in rc or 'case máy tính' in nm or 'máy tính bàn' in nm:
            return 'Máy tính bàn', 'PC'
        # 12. Suất ăn
        if 'suất ăn' in rc or 'suất ăn' in nm:
            return 'Máy đặt suất ăn', 'SA'
        return 'Khác', 'TB'

    room_full_name = {(r['floor'], r['raw_code']): r['name'] for r in all_rooms}

    cursor.execute("DELETE FROM device_movements")
    cursor.execute("DELETE FROM borrow_requests")
    cursor.execute("DELETE FROM devices")

    wb = openpyxl.load_workbook('data/Thiết bị 2022.xlsx', data_only=True)

    # Đếm số thứ tự liên tục theo từng loại tiền tố (prefix), bắt đầu từ Tầng 1
    seq_counter = {}
    device_records = []

    # Duyệt tuần tự các tầng từ Tầng 1 đến Tầng 6
    floor_sheets = ['Tầng 1', 'Tầng 2', 'Tầng 3', 'Tầng 4', 'Tầng 5', 'Tầng 6']

    for sheetname in floor_sheets:
        if sheetname not in wb.sheetnames:
            continue
        sheet = wb[sheetname]

        # Get room columns
        rooms_in_sheet = []
        for c in range(7, sheet.max_column + 1):
            val = sheet.cell(4, c).value
            if val and str(val).strip() != 'Tổng':
                rooms_in_sheet.append((c, str(val).strip()))

        for r in range(5, sheet.max_row + 1):
            raw_cat = sheet.cell(r, 2).value
            name = sheet.cell(r, 3).value
            model = sheet.cell(r, 4).value
            spec = sheet.cell(r, 5).value
            mfg = sheet.cell(r, 6).value

            if not name or not str(name).strip():
                continue

            name_clean = str(name).strip()
            model_clean = str(model).strip() if model else ""
            spec_clean = str(spec).strip() if spec else ""
            mfg_clean = str(mfg).strip() if mfg else ""

            cat_clean, prefix = categorize_device(raw_cat, name_clean)

            # Combine full title
            full_dev_name = name_clean
            if model_clean and model_clean not in full_dev_name:
                full_dev_name += f" ({model_clean})"

            full_spec = spec_clean
            if mfg_clean:
                full_spec = f"Hãng: {mfg_clean}" + (f" - {full_spec}" if full_spec else "")

            for col_idx, room_code in rooms_in_sheet:
                val = sheet.cell(r, col_idx).value
                if val and isinstance(val, (int, float)) and val > 0:
                    qty = int(val)
                    loc_name = room_full_name.get((sheetname, room_code), f"{room_code} ({sheetname})")

                    for _ in range(qty):
                        seq_counter[prefix] = seq_counter.get(prefix, 0) + 1
                        seq_num = seq_counter[prefix]
                        device_code = f"Sigma-{prefix}-{seq_num:03d}"

                        # Trạng thái sử dụng (Tình trạng sử dụng)
                        status = "Đang sử dụng"
                        if "Kho" in loc_name or "TUM" in loc_name:
                            status = "Sẵn sàng"

                        device_records.append((
                            device_code,
                            full_dev_name,
                            cat_clean,
                            loc_name,
                            status,
                            0,
                            "2022-08-15",
                            mfg_clean or "Dự án Đầu tư Thiết bị 2022",
                            full_spec or model_clean,
                            f"Lắp đặt tại {room_code} theo hồ sơ thiết bị {sheetname}",
                            None # assigned_user
                        ))

    print(f"Generated {len(device_records)} unique devices with Sigma- prefix.")

    cursor.executemany("""
        INSERT INTO devices (code, name, category, current_location, status, price, purchase_date, supplier, specification, notes, assigned_user)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, device_records)

    conn.commit()

    # Thêm phiếu mượn mẫu dựa trên cán bộ nhân viên thực tế từ file contact
    cursor.execute("SELECT code, fullname, department FROM users WHERE role = 'teacher' LIMIT 2")
    sample_users = cursor.fetchall()

    cursor.execute("SELECT code, name FROM devices WHERE category = 'Laptop giảng dạy' LIMIT 2")
    laptops = cursor.fetchall()

    if laptops and sample_users:
        u = sample_users[0]
        lt = laptops[0]
        cursor.execute("UPDATE devices SET status = 'Đang mượn', assigned_user = ? WHERE code = ?", (u['fullname'], lt['code']))
        cursor.execute("""
            INSERT INTO borrow_requests 
            (request_code, user_code, user_name, department, device_code, device_name, borrow_date, expected_return_date, purpose, status, approved_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("PM-20260920-001", u['code'], u['fullname'], u['department'], lt['code'], lt['name'], "2026-09-20", "2026-09-25", "Giảng dạy bài giảng điện tử thao giảng", "Đang mượn", "Nguyễn Tuấn Dũng"))

    # Lịch sử di chuyển mẫu
    cursor.execute("SELECT id, code, name, current_location FROM devices WHERE category = 'Máy chiếu & Phông chiếu' LIMIT 1")
    mc = cursor.fetchone()
    if mc:
        cursor.execute("""
            INSERT INTO device_movements (device_id, device_code, device_name, from_location, to_location, moved_by, move_date, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (mc['id'], mc['code'], mc['name'], "3F12 - Kho Công nghệ Thông tin (Kho IT)", mc['current_location'], "Ban Quản trị", "2026-09-15 14:00:00", "Bố trí lắp đặt phục vụ năm học mới"))

    # Log activity
    cursor.execute("""
        INSERT INTO activity_logs (user_name, action, target_type, details)
        VALUES ('Hệ thống', 'Nhập dữ liệu Sigma & Chuẩn hóa', 'system', 'Đã nạp 226 nhân sự từ SIGMA_EMAIL & CONTACT 2026.xlsx và chuẩn hóa mã thiết bị Sigma (PC, M, ROUTER...) theo thứ tự từ Tầng 1 đến Tầng 6')
    """)

    conn.commit()
    conn.close()
    print("ALL DATA IMPORTED & STANDARDIZED SUCCESSFULLY!")

if __name__ == '__main__':
    run_import()
