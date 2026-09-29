import os
import io
import csv
import json
import re
import sqlite3
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, jsonify, send_file, Response, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, init_db, log_activity
from seed_data import seed_database

app = Flask(__name__)
app.config['SECRET_KEY'] = 'qltb-school-equipment-secret-key-2026'

# Khởi tạo database và dữ liệu mẫu nếu chưa có
init_db()
seed_database()

# Helper lấy thông tin người dùng hiện tại từ session
def get_current_account():
    # 1. Kiểm tra session đăng nhập bảo mật
    acc = session.get('account')
    if acc:
        return acc
    # 2. Mặc định cho mọi truy cập chưa đăng nhập là guest (chỉ xem, không thể can thiệp dữ liệu)
    return {
        'id': 0,
        'username': 'guest',
        'fullname': 'Khách vãng lai',
        'role': 'guest',
        'is_authenticated': False
    }

# Decorator kiểm tra quyền Admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        acc = get_current_account()
        if acc.get('role') != 'admin':
            return jsonify({
                'error': 'Quyền truy cập bị từ chối! Bạn đang truy cập với vai trò Khách (Guest) - chỉ có quyền xem, không được phép thêm mới, chỉnh sửa hoặc xóa dữ liệu.',
                'require_admin': True,
                'current_role': acc.get('role')
            }), 403
        return f(*args, **kwargs)
    return decorated_function

# Helper dict conversion
def dict_from_row(row):
    return dict(row) if row else None

# Helper tính số ngày quá hạn
def calculate_overdue_days(expected_date_str, actual_date_str=None):
    if actual_date_str:
        return 0
    try:
        expected = datetime.strptime(expected_date_str, "%Y-%m-%d").date()
        today = date.today()
        if today > expected:
            return (today - expected).days
    except Exception:
        pass
    return 0

# --- VIEW ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download-csv-template')
def download_csv_template():
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_import.csv')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Thêm BOM UTF-8 để Excel trên Windows hiển thị đúng tiếng Việt
    bom_content = '\ufeff' + content
    return Response(
        bom_content,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment;filename=mau_nhap_thiet_bi.csv"}
    )

# --- AUTHENTICATION APIS (ĐĂNG NHẬP / ĐĂNG KÝ / PHÂN QUYỀN) ---
@app.route('/api/auth/me', methods=['GET'])
def get_current_user_info():
    acc = get_current_account()
    return jsonify(acc)

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    data = request.json or {}
    username = data.get('username', '').strip().lower()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'error': 'Vui lòng nhập tên đăng nhập và mật khẩu!'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE LOWER(username) = ?", (username,))
    account = cursor.fetchone()
    conn.close()

    if not account or not check_password_hash(account['password_hash'], password):
        return jsonify({'error': 'Tên đăng nhập hoặc mật khẩu không chính xác!'}), 401

    session['account'] = {
        'id': account['id'],
        'username': account['username'],
        'fullname': account['fullname'],
        'role': account['role'],
        'email': account['email'],
        'phone': account['phone'],
        'is_authenticated': True
    }

    log_activity("Đăng nhập", f"Người dùng {account['username']} ({account['fullname']}) đăng nhập vai trò {account['role'].upper()}", "auth", account['fullname'])
    return jsonify({
        'success': True,
        'account': session['account'],
        'message': f'Đăng nhập thành công với vai trò {account["role"].upper()}!'
    })

@app.route('/api/auth/register', methods=['POST'])
def auth_register():
    data = request.json or {}
    username = data.get('username', '').strip().lower()
    password = data.get('password', '').strip()
    fullname = data.get('fullname', '').strip()
    # Bảo mật: Tài khoản đăng ký mới BẮT BUỘC luôn là guest (chỉ xem), không cho phép đăng ký quyền admin
    role = 'guest'
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()

    if not username or len(username) < 3:
        return jsonify({'error': 'Tên đăng nhập phải có ít nhất 3 ký tự!'}), 400
    if not password or len(password) < 4:
        return jsonify({'error': 'Mật khẩu phải có ít nhất 4 ký tự!'}), 400
    if not fullname:
        return jsonify({'error': 'Vui lòng nhập họ và tên!'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM accounts WHERE LOWER(username) = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': f'Tên tài khoản "{username}" đã tồn tại. Vui lòng chọn tên khác!'}), 400

    pass_hash = generate_password_hash(password)
    cursor.execute("""
        INSERT INTO accounts (username, password_hash, fullname, role, email, phone)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, pass_hash, fullname, role, email, phone))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Tự động đăng nhập sau khi đăng ký
    session['account'] = {
        'id': new_id,
        'username': username,
        'fullname': fullname,
        'role': role,
        'email': email,
        'phone': phone,
        'is_authenticated': True
    }

    log_activity("Đăng ký tài khoản", f"Đăng ký tài khoản mới: {username} ({fullname}) - Vai trò {role.upper()}", "auth", fullname)
    return jsonify({
        'success': True,
        'account': session['account'],
        'message': f'Đăng ký tài khoản thành công với vai trò {role.upper()}!'
    })

@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():
    user = session.pop('account', None)
    if user:
        log_activity("Đăng xuất", f"Người dùng {user.get('username')} đăng xuất", "auth", user.get('fullname', 'User'))
    return jsonify({'success': True, 'message': 'Đã đăng xuất thành công!'})

@app.route('/api/auth/accounts', methods=['GET'])
@admin_required
def list_accounts():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, fullname, role, email, phone, created_at FROM accounts ORDER BY role ASC, username ASC")
    accs = [dict_from_row(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(accs)

# --- API STATS / DASHBOARD ---
@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    cursor = conn.cursor()

    # Tổng số thiết bị
    cursor.execute("SELECT COUNT(*) as total, COALESCE(SUM(price), 0) as total_value FROM devices")
    device_summary = cursor.fetchone()
    total_devices = device_summary['total']
    total_value = device_summary['total_value']

    # Thống kê theo trạng thái
    cursor.execute("SELECT status, COUNT(*) as count FROM devices GROUP BY status")
    status_counts = {row['status']: row['count'] for row in cursor.fetchall()}

    # Thống kê theo danh mục
    cursor.execute("SELECT category, COUNT(*) as count FROM devices GROUP BY category")
    category_counts = [{'category': row['category'], 'count': row['count']} for row in cursor.fetchall()]

    # Thống kê theo vị trí phòng ban
    cursor.execute("SELECT current_location, COUNT(*) as count FROM devices GROUP BY current_location ORDER BY count DESC LIMIT 8")
    location_counts = [{'location': row['current_location'], 'count': row['count']} for row in cursor.fetchall()]

    # Danh sách mượn quá hạn
    cursor.execute("""
        SELECT * FROM borrow_requests 
        WHERE status = 'Đang mượn' 
        ORDER BY expected_return_date ASC
    """)
    active_borrows = cursor.fetchall()
    overdue_list = []
    for b in active_borrows:
        overdue_days = calculate_overdue_days(b['expected_return_date'])
        if overdue_days > 0:
            item = dict_from_row(b)
            item['overdue_days'] = overdue_days
            overdue_list.append(item)

    # Top thiết bị mượn nhiều nhất
    cursor.execute("""
        SELECT device_code, device_name, COUNT(*) as borrow_count 
        FROM borrow_requests 
        GROUP BY device_code 
        ORDER BY borrow_count DESC LIMIT 5
    """)
    top_devices = [dict_from_row(r) for r in cursor.fetchall()]

    # Top giáo viên mượn nhiều nhất
    cursor.execute("""
        SELECT user_code, user_name, department, COUNT(*) as borrow_count 
        FROM borrow_requests 
        GROUP BY user_code 
        ORDER BY borrow_count DESC LIMIT 5
    """)
    top_teachers = [dict_from_row(r) for r in cursor.fetchall()]

    conn.close()

    return jsonify({
        'total_devices': total_devices,
        'total_value': total_value,
        'status_counts': {
            'ready': status_counts.get('Sẵn sàng', 0),
            'in_use': status_counts.get('Đang sử dụng', 0),
            'borrowed': status_counts.get('Đang mượn', 0),
            'broken': status_counts.get('Hỏng', 0),
            'maintenance': status_counts.get('Bảo trì', 0),
            'disposed': status_counts.get('Đã thanh lý', 0)
        },
        'category_counts': category_counts,
        'location_counts': location_counts,
        'overdue_count': len(overdue_list),
        'overdue_list': overdue_list,
        'top_devices': top_devices,
        'top_teachers': top_teachers
    })

# --- API DEVICES ---
@app.route('/api/devices', methods=['GET'])
def list_devices():
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()
    status = request.args.get('status', '').strip()
    location = request.args.get('location', '').strip()
    floor = request.args.get('floor', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM devices WHERE 1=1"
    params = []

    if search:
        query += " AND (code LIKE ? OR name LIKE ? OR specification LIKE ? OR supplier LIKE ? OR assigned_user LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term, term])

    if category and category != 'all':
        query += " AND category = ?"
        params.append(category)

    if status and status != 'all':
        query += " AND status = ?"
        params.append(status)

    if location and location != 'all':
        query += " AND current_location = ?"
        params.append(location)

    if floor and floor != 'all':
        query += " AND current_location IN (SELECT name FROM locations WHERE floor = ?)"
        params.append(floor)

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    devices = [dict_from_row(r) for r in cursor.fetchall()]
    conn.close()

    return jsonify(devices)

def get_device_category_prefix(category_name):
    if not category_name:
        return 'TB'
    c = category_name.lower()
    if 'màn hình' in c: return 'M'
    if 'máy tính bàn' in c or 'case' in c: return 'PC'
    if 'mạng' in c or 'router' in c or 'switch' in c: return 'ROUTER'
    if 'unifi' in c or 'wifi' in c: return 'WF'
    if 'laptop' in c: return 'LT'
    if 'in' in c or 'photo' in c: return 'PRN'
    if 'chiếu' in c: return 'MC'
    if 'camera' in c: return 'CAM'
    if 'âm thanh' in c: return 'AT'
    if 'chấm công' in c or 'thẻ' in c: return 'CC'
    if 'server' in c or 'máy chủ' in c: return 'SRV'
    if 'suất ăn' in c: return 'SA'
    return 'TB'

@app.route('/api/devices/suggest-code', methods=['GET'])
def suggest_device_code():
    category = request.args.get('category', '').strip()
    prefix = get_device_category_prefix(category)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM devices WHERE code LIKE ?", (f"Sigma-{prefix}-%",))
    codes = [r['code'] for r in cursor.fetchall()]
    conn.close()

    max_num = 0
    pattern = re.compile(rf"^Sigma-{prefix}-(\d+)$", re.IGNORECASE)
    for c in codes:
        m = pattern.match(c)
        if m:
            val = int(m.group(1))
            if val > max_num:
                max_num = val

    suggested = f"Sigma-{prefix}-{max_num + 1:03d}"
    return jsonify({'prefix': prefix, 'suggested_code': suggested, 'next_seq': max_num + 1})

@app.route('/api/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
    device = cursor.fetchone()
    if not device:
        conn.close()
        return jsonify({'error': 'Không tìm thấy thiết bị'}), 404

    result = dict_from_row(device)

    # Lấy lịch sử di chuyển
    cursor.execute(
        "SELECT * FROM device_movements WHERE device_id = ? ORDER BY move_date DESC",
        (device_id,)
    )
    result['movements'] = [dict_from_row(r) for r in cursor.fetchall()]

    # Lấy lịch sử mượn
    cursor.execute(
        "SELECT * FROM borrow_requests WHERE device_code = ? ORDER BY borrow_date DESC",
        (result['code'],)
    )
    result['borrows'] = [dict_from_row(r) for r in cursor.fetchall()]

    conn.close()
    return jsonify(result)

@app.route('/api/devices', methods=['POST'])
@admin_required
def add_device():
    data = request.json or {}
    code = data.get('code', '').strip().upper()
    name = data.get('name', '').strip()
    category = data.get('category', '').strip()
    current_location = data.get('current_location', '').strip()
    status = data.get('status', 'Sẵn sàng').strip()
    price = float(data.get('price') or 0)
    purchase_date = data.get('purchase_date', '').strip() or date.today().strftime('%Y-%m-%d')
    supplier = data.get('supplier', '').strip()
    specification = data.get('specification', '').strip()
    notes = data.get('notes', '').strip()
    assigned_user = data.get('assigned_user', '').strip() or None

    if not code or not name or not category or not current_location:
        return jsonify({'error': 'Vui lòng điền đầy đủ Mã thiết bị, Tên thiết bị, Danh mục và Vị trí!'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Kiểm tra trùng lặp mã thiết bị
    cursor.execute("SELECT id FROM devices WHERE code = ?", (code,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': f'Mã thiết bị "{code}" đã tồn tại trong hệ thống! Vui lòng chọn mã khác.'}), 400

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO devices (code, name, category, current_location, status, price, purchase_date, supplier, specification, notes, assigned_user, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (code, name, category, current_location, status, price, purchase_date, supplier, specification, notes, assigned_user, now_str, now_str))

    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    log_activity("Thêm thiết bị", f"Thêm mới thiết bị {code} - {name} tại vị trí {current_location}", "device")
    return jsonify({'success': True, 'id': new_id, 'message': f'Thêm thiết bị {code} thành công!'})

@app.route('/api/devices/<int:device_id>', methods=['PUT'])
@admin_required
def update_device(device_id):
    data = request.json or {}
    code = data.get('code', '').strip().upper()
    name = data.get('name', '').strip()
    category = data.get('category', '').strip()
    current_location = data.get('current_location', '').strip()
    status = data.get('status', 'Sẵn sàng').strip()
    price = float(data.get('price') or 0)
    purchase_date = data.get('purchase_date', '').strip()
    supplier = data.get('supplier', '').strip()
    specification = data.get('specification', '').strip()
    notes = data.get('notes', '').strip()
    assigned_user = data.get('assigned_user', '').strip() or None

    if not code or not name or not category or not current_location:
        return jsonify({'error': 'Vui lòng điền đầy đủ các thông tin bắt buộc!'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Kiểm tra thiết bị có tồn tại
    cursor.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
    old_device = cursor.fetchone()
    if not old_device:
        conn.close()
        return jsonify({'error': 'Không tìm thấy thiết bị cần sửa!'}), 404

    # Kiểm tra trùng lặp mã với thiết bị khác
    cursor.execute("SELECT id FROM devices WHERE code = ? AND id != ?", (code, device_id))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': f'Mã thiết bị "{code}" đã được sử dụng cho thiết bị khác!'}), 400

    old_location = old_device['current_location']
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Nếu vị trí thay đổi qua form sửa thông tin, tự động ghi log di chuyển
    if old_location != current_location:
        cursor.execute("""
            INSERT INTO device_movements (device_id, device_code, device_name, from_location, to_location, moved_by, move_date, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (device_id, code, name, old_location, current_location, 'Quản trị viên', now_str, 'Cập nhật vị trí từ hồ sơ thiết bị'))

    cursor.execute("""
        UPDATE devices 
        SET code = ?, name = ?, category = ?, current_location = ?, status = ?, price = ?, 
            purchase_date = ?, supplier = ?, specification = ?, notes = ?, assigned_user = ?, updated_at = ?
        WHERE id = ?
    """, (code, name, category, current_location, status, price, purchase_date, supplier, specification, notes, assigned_user, now_str, device_id))

    conn.commit()
    conn.close()

    log_activity("Cập nhật thiết bị", f"Cập nhật thông tin thiết bị {code} - {name}", "device")
    return jsonify({'success': True, 'message': 'Cập nhật thiết bị thành công!'})

@app.route('/api/devices/<int:device_id>', methods=['DELETE'])
@admin_required
def delete_device(device_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
    device = cursor.fetchone()
    if not device:
        conn.close()
        return jsonify({'error': 'Không tìm thấy thiết bị!'}), 404

    if device['status'] == 'Đang mượn':
        conn.close()
        return jsonify({'error': 'Không thể xóa thiết bị đang được mượn! Vui lòng thu hồi thiết bị trước khi xóa.'}), 400

    cursor.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    conn.commit()
    conn.close()

    log_activity("Xóa thiết bị", f"Xóa thiết bị {device['code']} - {device['name']}", "device")
    return jsonify({'success': True, 'message': f'Đã xóa thiết bị {device["code"]}!'})

# --- API DI CHUYỂN PHÂN LOẠI THIẾT BỊ ---
@app.route('/api/devices/change-category', methods=['POST'])
@admin_required
def change_device_category():
    data = request.json or {}
    device_id = data.get('device_id')
    device_ids = data.get('device_ids') or ([device_id] if device_id else [])
    new_category = data.get('category', '').strip()

    if not device_ids or not new_category:
        return jsonify({'error': 'Vui lòng cung cấp danh sách thiết bị và phân loại mới!'}), 400

    conn = get_db()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    updated_count = 0
    for did in device_ids:
        cursor.execute("UPDATE devices SET category = ?, updated_at = ? WHERE id = ?", (new_category, now_str, did))
        if cursor.rowcount > 0:
            updated_count += 1

    conn.commit()
    conn.close()

    log_activity("Di chuyển phân loại", f"Chuyển {updated_count} thiết bị sang phân loại '{new_category}'", "category")
    return jsonify({
        'success': True,
        'updated_count': updated_count,
        'message': f'Đã chuyển {updated_count} thiết bị sang phân loại "{new_category}" thành công!'
    })

# --- API DI CHUYỂN THIẾT BỊ (MOVEMENT TRACKING) ---
@app.route('/api/devices/move', methods=['POST'])
@admin_required
def move_device():
    data = request.json or {}
    device_code = data.get('device_code', '').strip().upper()
    to_location = data.get('to_location', '').strip()
    moved_by = data.get('moved_by', '').strip() or 'Quản trị viên'
    reason = data.get('reason', '').strip()

    if not device_code or not to_location or not reason:
        return jsonify({'error': 'Vui lòng cung cấp Mã thiết bị, Vị trí mới và Lý do di chuyển!'}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM devices WHERE code = ?", (device_code,))
    device = cursor.fetchone()
    if not device:
        conn.close()
        return jsonify({'error': f'Không tìm thấy thiết bị với mã "{device_code}"!'}), 404

    from_location = device['current_location']
    if from_location == to_location:
        conn.close()
        return jsonify({'error': f'Thiết bị hiện tại đã ở vị trí "{to_location}" rồi!'}), 400

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. Thêm bản ghi lịch sử di chuyển
    cursor.execute("""
        INSERT INTO device_movements (device_id, device_code, device_name, from_location, to_location, moved_by, move_date, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (device['id'], device['code'], device['name'], from_location, to_location, moved_by, now_str, reason))

    # 2. Cập nhật vị trí hiện tại trong bảng devices
    cursor.execute("""
        UPDATE devices SET current_location = ?, updated_at = ? WHERE id = ?
    """, (to_location, now_str, device['id']))

    conn.commit()
    conn.close()

    log_activity("Di chuyển thiết bị", f"Chuyển {device['code']} từ [{from_location}] sang [{to_location}]. Lý do: {reason}", "movement", moved_by)
    return jsonify({
        'success': True,
        'message': f'Đã chuyển thiết bị {device["code"]} từ "{from_location}" sang "{to_location}" thành công!',
        'from_location': from_location,
        'to_location': to_location
    })

@app.route('/api/movements', methods=['GET'])
def get_movements():
    search = request.args.get('search', '').strip()
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM device_movements WHERE 1=1"
    params = []
    if search:
        query += " AND (device_code LIKE ? OR device_name LIKE ? OR from_location LIKE ? OR to_location LIKE ? OR moved_by LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term, term])

    query += " ORDER BY move_date DESC, id DESC"
    cursor.execute(query, params)
    movements = [dict_from_row(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(movements)

# --- API IMPORT CSV / EXCEL ---
@app.route('/api/devices/import-csv', methods=['POST'])
@admin_required
def import_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'Không tìm thấy tệp CSV được tải lên!'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Chưa chọn tệp!'}), 400

    content_bytes = file.read()
    # Decode thử UTF-8 với fallback sang Latin-1
    content_text = None
    for enc in ['utf-8-sig', 'utf-8', 'cp1258', 'latin-1']:
        try:
            content_text = content_bytes.decode(enc)
            break
        except Exception:
            continue

    if not content_text:
        return jsonify({'error': 'Không thể đọc nội dung file. Vui lòng đảm bảo tệp định dạng CSV UTF-8.'}), 400

    csv_reader = csv.reader(io.StringIO(content_text))
    rows = list(csv_reader)
    if not rows or len(rows) < 2:
        return jsonify({'error': 'File CSV không có dữ liệu hoặc chỉ có tiêu đề!'}), 400

    headers = [h.strip().lower() for h in rows[0]]
    # Mapping header linh hoạt
    col_map = {}
    for idx, h in enumerate(headers):
        if 'mã' in h or 'code' in h:
            col_map['code'] = idx
        elif 'tên' in h or 'name' in h:
            col_map['name'] = idx
        elif 'danh mục' in h or 'loại' in h or 'category' in h:
            col_map['category'] = idx
        elif 'vị trí' in h or 'phòng' in h or 'location' in h:
            col_map['location'] = idx
        elif 'tình trạng' in h or 'trạng thái' in h or 'status' in h:
            col_map['status'] = idx
        elif 'giá' in h or 'price' in h:
            col_map['price'] = idx
        elif 'ngày' in h or 'date' in h:
            col_map['purchase_date'] = idx
        elif 'cung cấp' in h or 'supplier' in h:
            col_map['supplier'] = idx
        elif 'thông số' in h or 'spec' in h:
            col_map['specification'] = idx
        elif 'ghi chú' in h or 'note' in h:
            col_map['notes'] = idx

    if 'code' not in col_map or 'name' not in col_map:
        return jsonify({'error': 'File CSV bắt buộc phải có cột "Mã thiết bị" và "Tên thiết bị"!'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Lấy toàn bộ mã thiết bị hiện có để kiểm tra trùng
    cursor.execute("SELECT code FROM devices")
    existing_codes = set(r['code'].upper() for r in cursor.fetchall())

    file_codes = set()
    success_count = 0
    errors = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for row_idx, row in enumerate(rows[1:], start=2):
        if not row or all(not cell.strip() for cell in row):
            continue

        def get_val(key, default=''):
            idx = col_map.get(key)
            if idx is not None and idx < len(row):
                return row[idx].strip()
            return default

        code = get_val('code').upper()
        name = get_val('name')
        category = get_val('category', 'Khác')
        location = get_val('location', 'Kho Thiết bị Trung tâm')
        status = get_val('status', 'Sẵn sàng')
        price_raw = get_val('price', '0').replace(',', '').replace('.', '').replace('đ', '').replace('VND', '').strip()
        try:
            price = float(price_raw) if price_raw else 0.0
        except Exception:
            price = 0.0
        purchase_date = get_val('purchase_date', date.today().strftime('%Y-%m-%d'))
        supplier = get_val('supplier', '')
        spec = get_val('specification', '')
        notes = get_val('notes', '')

        if not code or not name:
            errors.append(f'Dòng {row_idx}: Thiếu Mã thiết bị hoặc Tên thiết bị.')
            continue

        if code in existing_codes:
            errors.append(f'Dòng {row_idx}: Mã "{code}" đã tồn tại trong cơ sở dữ liệu (Trùng lặp)!')
            continue

        if code in file_codes:
            errors.append(f'Dòng {row_idx}: Mã "{code}" bị lặp lại nhiều lần ngay trong file CSV!')
            continue

        try:
            cursor.execute("""
                INSERT INTO devices (code, name, category, current_location, status, price, purchase_date, supplier, specification, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (code, name, category, location, status, price, purchase_date, supplier, spec, notes, now_str, now_str))
            file_codes.add(code)
            existing_codes.add(code)
            success_count += 1
        except Exception as e:
            errors.append(f'Dòng {row_idx}: Lỗi hệ thống khi lưu "{code}" ({str(e)})')

    conn.commit()
    conn.close()

    log_activity("Nhập thiết bị CSV", f"Nhập thành công {success_count} thiết bị từ file {file.filename}", "device")

    return jsonify({
        'success': True,
        'success_count': success_count,
        'error_count': len(errors),
        'errors': errors,
        'message': f'Đã nhập thành công {success_count} thiết bị!' + (f' Có {len(errors)} dòng bị bỏ qua do lỗi/trùng lặp.' if errors else '')
    })

# --- API MƯỢN - TRẢ THIẾT BỊ (BORROW & RETURN) ---
@app.route('/api/borrow', methods=['GET'])
def list_borrow_requests():
    status = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM borrow_requests WHERE 1=1"
    params = []

    if status and status != 'all':
        query += " AND status = ?"
        params.append(status)

    if search:
        query += " AND (request_code LIKE ? OR user_code LIKE ? OR user_name LIKE ? OR device_code LIKE ? OR device_name LIKE ? OR department LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term, term, term])

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()

    result = []
    for r in rows:
        item = dict_from_row(r)
        item['overdue_days'] = calculate_overdue_days(item['expected_return_date'], item['actual_return_date'])
        result.append(item)

    conn.close()
    return jsonify(result)

@app.route('/api/borrow', methods=['POST'])
def create_borrow_request():
    data = request.json or {}
    user_code = data.get('user_code', '').strip().upper()
    device_code = data.get('device_code', '').strip().upper()
    borrow_date = data.get('borrow_date', '').strip() or date.today().strftime('%Y-%m-%d')
    expected_return_date = data.get('expected_return_date', '').strip()
    purpose = data.get('purpose', '').strip()
    auto_approve = data.get('auto_approve', False)

    if not user_code or not device_code or not expected_return_date:
        return jsonify({'error': 'Vui lòng cung cấp đầy đủ Mã giáo viên, Mã thiết bị và Hạn trả!'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # 1. Kiểm tra giáo viên
    cursor.execute("SELECT * FROM users WHERE code = ?", (user_code,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return jsonify({'error': f'Không tìm thấy giáo viên/cán bộ có mã "{user_code}" trong hệ thống!'}), 404

    # 2. Kiểm tra thiết bị
    cursor.execute("SELECT * FROM devices WHERE code = ?", (device_code,))
    device = cursor.fetchone()
    if not device:
        conn.close()
        return jsonify({'error': f'Không tìm thấy thiết bị có mã "{device_code}" trong hệ thống!'}), 404

    # Kiểm tra trạng thái thiết bị
    if device['status'] == 'Đang mượn':
        conn.close()
        return jsonify({'error': f'Thiết bị "{device_code}" đang được mượn bởi người khác! Không thể tạo phiếu mượn.'}), 400
    if device['status'] in ['Hỏng', 'Bảo trì', 'Đã thanh lý']:
        conn.close()
        return jsonify({'error': f'Thiết bị "{device_code}" đang ở trạng thái "{device["status"]}", không thể xuất mượn!'}), 400

    # 3. Tạo mã phiếu mượn duy nhất: PM-YYYYMMDD-XXXX
    date_prefix = datetime.now().strftime("%Y%m%d")
    cursor.execute("SELECT COUNT(*) as cnt FROM borrow_requests WHERE request_code LIKE ?", (f"PM-{date_prefix}%",))
    count_today = cursor.fetchone()['cnt'] + 1
    request_code = f"PM-{date_prefix}-{count_today:03d}"

    initial_status = 'Đang mượn' if auto_approve else 'Chờ duyệt'
    approved_by = 'Quản trị viên' if auto_approve else None

    cursor.execute("""
        INSERT INTO borrow_requests 
        (request_code, user_code, user_name, department, device_code, device_name, borrow_date, expected_return_date, purpose, status, approved_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (request_code, user['code'], user['fullname'], user['department'], device['code'], device['name'], borrow_date, expected_return_date, purpose, initial_status, approved_by))

    # Nếu được tự động duyệt ngay thì cập nhật luôn trạng thái thiết bị thành "Đang mượn"
    if auto_approve:
        cursor.execute("UPDATE devices SET status = 'Đang mượn', updated_at = ? WHERE id = ?", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), device['id']))

    conn.commit()
    conn.close()

    log_activity(
        "Tạo phiếu mượn",
        f"Mã phiếu {request_code}: GV {user['fullname']} ({user['code']}) mượn thiết bị {device['code']} - {device['name']}",
        "borrow",
        user['fullname']
    )

    return jsonify({
        'success': True,
        'request_code': request_code,
        'message': f'Tạo phiếu mượn {request_code} thành công!' + (' (Đã duyệt)' if auto_approve else ' (Đang chờ ban quản trị duyệt)')
    })

@app.route('/api/borrow/<int:borrow_id>/approve', methods=['PUT'])
@admin_required
def approve_borrow(borrow_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM borrow_requests WHERE id = ?", (borrow_id,))
    req = cursor.fetchone()
    if not req:
        conn.close()
        return jsonify({'error': 'Không tìm thấy phiếu mượn!'}), 404

    if req['status'] != 'Chờ duyệt':
        conn.close()
        return jsonify({'error': f'Phiếu mượn đang ở trạng thái "{req["status"]}", không thể duyệt!'}), 400

    # Kiểm tra thiết bị xem có còn sẵn sàng không
    cursor.execute("SELECT * FROM devices WHERE code = ?", (req['device_code'],))
    device = cursor.fetchone()
    if not device:
        conn.close()
        return jsonify({'error': 'Không tìm thấy thông tin thiết bị!'}), 404

    if device['status'] == 'Đang mượn':
        conn.close()
        return jsonify({'error': 'Thiết bị này đã có người khác mượn rồi!'}), 400

    # Cập nhật phiếu mượn
    cursor.execute("""
        UPDATE borrow_requests SET status = 'Đang mượn', approved_by = 'Quản trị viên' WHERE id = ?
    """, (borrow_id,))

    # Cập nhật trạng thái thiết bị
    cursor.execute("""
        UPDATE devices SET status = 'Đang mượn', updated_at = ? WHERE code = ?
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), req['device_code']))

    conn.commit()
    conn.close()

    log_activity("Duyệt phiếu mượn", f"Duyệt phiếu {req['request_code']} cho {req['user_name']} mượn {req['device_code']}", "borrow")
    return jsonify({'success': True, 'message': f'Đã duyệt phiếu mượn {req["request_code"]}!'})

@app.route('/api/borrow/<int:borrow_id>/reject', methods=['PUT'])
@admin_required
def reject_borrow(borrow_id):
    data = request.json or {}
    reason = data.get('reason', 'Không đủ điều kiện hoặc thiết bị cần ưu tiên cho công việc khác')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM borrow_requests WHERE id = ?", (borrow_id,))
    req = cursor.fetchone()
    if not req:
        conn.close()
        return jsonify({'error': 'Không tìm thấy phiếu mượn!'}), 404

    cursor.execute("""
        UPDATE borrow_requests SET status = 'Từ chối', notes = ?, approved_by = 'Quản trị viên' WHERE id = ?
    """, (f"Lý do từ chối: {reason}", borrow_id))

    conn.commit()
    conn.close()

    log_activity("Từ chối phiếu mượn", f"Từ chối phiếu {req['request_code']} của {req['user_name']}", "borrow")
    return jsonify({'success': True, 'message': f'Đã từ chối phiếu mượn {req["request_code"]}!'})

@app.route('/api/borrow/<int:borrow_id>/return', methods=['PUT'])
@admin_required
def return_borrow(borrow_id):
    data = request.json or {}
    actual_return_date = data.get('actual_return_date', '').strip() or date.today().strftime('%Y-%m-%d')
    return_condition = data.get('return_condition', 'Tốt').strip()
    notes = data.get('notes', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM borrow_requests WHERE id = ?", (borrow_id,))
    req = cursor.fetchone()
    if not req:
        conn.close()
        return jsonify({'error': 'Không tìm thấy phiếu mượn!'}), 404

    if req['status'] != 'Đang mượn':
        conn.close()
        return jsonify({'error': 'Chỉ có thể ghi nhận trả cho phiếu đang ở trạng thái "Đang mượn"!'}), 400

    # 1. Cập nhật phiếu mượn
    cursor.execute("""
        UPDATE borrow_requests 
        SET status = 'Đã trả', actual_return_date = ?, return_condition = ?, notes = COALESCE(notes || ' | ', '') || ?
        WHERE id = ?
    """, (actual_return_date, return_condition, f"Tình trạng khi trả: {return_condition}. {notes}", borrow_id))

    # 2. Cập nhật trạng thái thiết bị dựa vào tình trạng khi trả
    new_device_status = 'Sẵn sàng'
    if return_condition in ['Hư hỏng nhẹ', 'Hỏng nặng']:
        new_device_status = 'Hỏng'
    elif return_condition == 'Mất phụ kiện':
        new_device_status = 'Bảo trì'

    cursor.execute("""
        UPDATE devices SET status = ?, updated_at = ? WHERE code = ?
    """, (new_device_status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), req['device_code']))

    conn.commit()
    conn.close()

    log_activity(
        "Ghi nhận trả thiết bị",
        f"Thu hồi thiết bị {req['device_code']} từ {req['user_name']} (Mã phiếu {req['request_code']}). Tình trạng: {return_condition}",
        "borrow"
    )

    return jsonify({
        'success': True,
        'message': f'Ghi nhận hoàn trả phiếu {req["request_code"]} thành công! Trạng thái thiết bị hiện tại: {new_device_status}'
    })

# --- API USERS & LOCATIONS & CATEGORIES ---
@app.route('/api/users', methods=['GET'])
def list_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY department ASC, fullname ASC")
    users = [dict_from_row(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(users)

@app.route('/api/users', methods=['POST'])
@admin_required
def add_user():
    data = request.json or {}
    code = data.get('code', '').strip().upper()
    fullname = data.get('fullname', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    role = data.get('role', 'teacher').strip()
    department = data.get('department', '').strip()

    if not code or not fullname or not department:
        return jsonify({'error': 'Vui lòng điền đầy đủ Mã giáo viên/cán bộ, Họ tên và Phòng ban/Bộ môn!'}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE code = ?", (code,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': f'Mã người dùng/giáo viên "{code}" đã tồn tại!'}), 400

    cursor.execute("""
        INSERT INTO users (code, fullname, email, phone, role, department)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (code, fullname, email, phone, role, department))

    conn.commit()
    conn.close()

    log_activity("Thêm người dùng", f"Thêm giáo viên/cán bộ {code} - {fullname} ({department})", "user")
    return jsonify({'success': True, 'message': f'Thêm người dùng {code} thành công!'})

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    data = request.json or {}
    code = data.get('code', '').strip().upper()
    fullname = data.get('fullname', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    role = data.get('role', 'teacher').strip()
    department = data.get('department', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE code = ? AND id != ?", (code, user_id))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': f'Mã "{code}" đã được người khác sử dụng!'}), 400

    cursor.execute("""
        UPDATE users SET code = ?, fullname = ?, email = ?, phone = ?, role = ?, department = ? WHERE id = ?
    """, (code, fullname, email, phone, role, department, user_id))

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Cập nhật thông tin thành công!'})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Đã xóa người dùng!'})

# --- API QUẢN LÝ PHÂN LOẠI / DANH MỤC (CATEGORIES) ---
@app.route('/api/categories', methods=['GET'])
def list_categories():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories ORDER BY id ASC")
    categories = [dict_from_row(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(categories)

@app.route('/api/categories', methods=['POST'])
@admin_required
def add_category():
    data = request.json or {}
    name = data.get('name', '').strip()
    icon = data.get('icon', 'package').strip() or 'package'

    if not name:
        return jsonify({'error': 'Tên danh mục phân loại không được để trống!'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM categories WHERE name = ?", (name,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': f'Phân loại danh mục "{name}" đã tồn tại!'}), 400

    cursor.execute("INSERT INTO categories (name, icon) VALUES (?, ?)", (name, icon))
    conn.commit()
    conn.close()

    log_activity("Thêm phân loại", f"Tạo mới phân loại thiết bị: {name}", "category")
    return jsonify({'success': True, 'message': f'Thêm phân loại "{name}" thành công!'})

@app.route('/api/categories/<int:cat_id>', methods=['PUT'])
@admin_required
def update_category(cat_id):
    data = request.json or {}
    new_name = data.get('name', '').strip()
    icon = data.get('icon', '').strip()

    if not new_name:
        return jsonify({'error': 'Tên danh mục không được để trống!'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE id = ?", (cat_id,))
    old_cat = cursor.fetchone()
    if not old_cat:
        conn.close()
        return jsonify({'error': 'Không tìm thấy phân loại danh mục!'}), 404

    old_name = old_cat['name']
    cursor.execute("UPDATE categories SET name = ?, icon = COALESCE(NULLIF(?, ''), icon) WHERE id = ?", (new_name, icon, cat_id))
    # Đồng bộ sang các thiết bị đang mang tên danh mục cũ
    cursor.execute("UPDATE devices SET category = ? WHERE category = ?", (new_name, old_name))
    conn.commit()
    conn.close()

    log_activity("Sửa phân loại", f"Đổi tên phân loại từ '{old_name}' thành '{new_name}'", "category")
    return jsonify({'success': True, 'message': f'Cập nhật phân loại thành "{new_name}" thành công!'})

@app.route('/api/categories/<int:cat_id>', methods=['DELETE'])
@admin_required
def delete_category(cat_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE id = ?", (cat_id,))
    cat = cursor.fetchone()
    if not cat:
        conn.close()
        return jsonify({'error': 'Không tìm thấy danh mục!'}), 404

    cat_name = cat['name']
    cursor.execute("SELECT COUNT(*) as cnt FROM devices WHERE category = ?", (cat_name,))
    dev_count = cursor.fetchone()['cnt']
    if dev_count > 0:
        conn.close()
        return jsonify({'error': f'Không thể xóa vì còn {dev_count} thiết bị đang thuộc phân loại "{cat_name}". Hãy chuyển phân loại của các thiết bị này trước!'}), 400

    cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()

    log_activity("Xóa phân loại", f"Xóa phân loại '{cat_name}'", "category")
    return jsonify({'success': True, 'message': f'Đã xóa phân loại "{cat_name}"!'})

# --- API QUẢN LÝ PHÒNG HỌC & VỊ TRÍ (LOCATIONS) ---
@app.route('/api/locations', methods=['GET'])
def list_locations():
    floor = request.args.get('floor')
    conn = get_db()
    cursor = conn.cursor()
    if floor and floor != 'all':
        cursor.execute("SELECT * FROM locations WHERE floor = ? ORDER BY code ASC", (floor,))
    else:
        cursor.execute("SELECT * FROM locations ORDER BY floor ASC, code ASC")
    locations = [dict_from_row(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(locations)

@app.route('/api/locations', methods=['POST'])
@admin_required
def add_location():
    data = request.json or {}
    code = data.get('code', '').strip().upper()
    name = data.get('name', '').strip()
    loc_type = data.get('type', 'Phòng học & Lớp học').strip()
    floor = data.get('floor', 'Tầng 1').strip()
    manager_name = data.get('manager_name', '').strip()
    description = data.get('description', '').strip()

    if not code or not name:
        return jsonify({'error': 'Vui lòng nhập Mã và Tên phòng ban/vị trí!'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM locations WHERE code = ?", (code,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': f'Mã vị trí/phòng "{code}" đã tồn tại!'}), 400

    cursor.execute("""
        INSERT INTO locations (code, name, type, floor, manager_name, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (code, name, loc_type, floor, manager_name, description))
    conn.commit()
    conn.close()

    log_activity("Thêm phòng", f"Thêm mới phòng học/vị trí {code} - {name} ({floor}, Loại: {loc_type})", "location")
    return jsonify({'success': True, 'message': f'Thêm phòng {name} thành công!'})

@app.route('/api/locations/<int:loc_id>', methods=['PUT'])
@admin_required
def update_location(loc_id):
    data = request.json or {}
    code = data.get('code', '').strip().upper()
    name = data.get('name', '').strip()
    loc_type = data.get('type', 'Phòng học & Lớp học').strip()
    floor = data.get('floor', 'Tầng 1').strip()
    manager_name = data.get('manager_name', '').strip()
    description = data.get('description', '').strip()

    if not code or not name:
        return jsonify({'error': 'Mã phòng và Tên phòng không được để trống!'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM locations WHERE id = ?", (loc_id,))
    old_loc = cursor.fetchone()
    if not old_loc:
        conn.close()
        return jsonify({'error': 'Không tìm thấy phòng!'}), 404

    # Kiểm tra trùng mã
    cursor.execute("SELECT id FROM locations WHERE code = ? AND id != ?", (code, loc_id))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': f'Mã vị trí "{code}" đã được sử dụng cho phòng khác!'}), 400

    old_name = old_loc['name']
    cursor.execute("""
        UPDATE locations 
        SET code = ?, name = ?, type = ?, floor = ?, manager_name = ?, description = ?
        WHERE id = ?
    """, (code, name, loc_type, floor, manager_name, description, loc_id))

    # Nếu đổi tên phòng, cập nhật cả cột current_location trong devices
    if old_name != name:
        cursor.execute("UPDATE devices SET current_location = ? WHERE current_location = ?", (name, old_name))

    conn.commit()
    conn.close()

    log_activity("Sửa phòng", f"Cập nhật thông tin phòng {code} - {name} (Loại: {loc_type})", "location")
    return jsonify({'success': True, 'message': f'Cập nhật phòng "{name}" thành công!'})

# Chỉnh sửa nhanh Loại ở phần hiển thị chỗ phòng
@app.route('/api/locations/<int:loc_id>/type', methods=['PATCH', 'PUT'])
@admin_required
def update_location_type(loc_id):
    data = request.json or {}
    new_type = data.get('type', '').strip()
    if not new_type:
        return jsonify({'error': 'Loại phòng không được để trống!'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM locations WHERE id = ?", (loc_id,))
    loc = cursor.fetchone()
    if not loc:
        conn.close()
        return jsonify({'error': 'Không tìm thấy phòng!'}), 404

    cursor.execute("UPDATE locations SET type = ? WHERE id = ?", (new_type, loc_id))
    conn.commit()
    conn.close()

    log_activity("Đổi loại phòng", f"Cập nhật loại phòng cho '{loc['name']}' thành '{new_type}'", "location")
    return jsonify({'success': True, 'type': new_type, 'message': f'Đã cập nhật loại phòng thành "{new_type}" thành công!'})

@app.route('/api/locations/<int:loc_id>', methods=['DELETE'])
@admin_required
def delete_location(loc_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM locations WHERE id = ?", (loc_id,))
    loc = cursor.fetchone()
    if not loc:
        conn.close()
        return jsonify({'error': 'Không tìm thấy phòng!'}), 404

    # Kiểm tra thiết bị trong phòng
    cursor.execute("SELECT COUNT(*) as count FROM devices WHERE current_location = ?", (loc['name'],))
    dev_count = cursor.fetchone()['count']
    if dev_count > 0:
        conn.close()
        return jsonify({'error': f'Không thể xóa phòng "{loc["name"]}" vì đang có {dev_count} thiết bị tại đây. Vui lòng di chuyển thiết bị trước khi xóa phòng!'}), 400

    cursor.execute("DELETE FROM locations WHERE id = ?", (loc_id,))
    conn.commit()
    conn.close()

    log_activity("Xóa phòng", f"Xóa phòng học/vị trí {loc['code']} - {loc['name']}", "location")
    return jsonify({'success': True, 'message': f'Đã xóa phòng "{loc["name"]}" thành công!'})

@app.route('/api/floors', methods=['GET'])
def list_floors():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT floor FROM locations ORDER BY floor ASC")
    floors = [r['floor'] for r in cursor.fetchall() if r['floor']]
    conn.close()
    return jsonify(floors)

@app.route('/api/standard-devices', methods=['GET'])
def list_standard_devices():
    # Danh sách thiết bị chuẩn trích xuất từ Thiết bị 2022
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'total_devices_extracted.json')
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return jsonify(data)
    return jsonify([])

# --- SYSTEM ACTIVITY LOGS & BACKUP/RESTORE ---
@app.route('/api/logs', methods=['GET'])
def list_logs():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activity_logs ORDER BY created_at DESC LIMIT 50")
    logs = [dict_from_row(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(logs)

@app.route('/api/backup', methods=['GET'])
def backup_data():
    conn = get_db()
    cursor = conn.cursor()
    tables = ['users', 'locations', 'categories', 'devices', 'device_movements', 'borrow_requests', 'activity_logs']
    backup = {}
    for t in tables:
        cursor.execute(f"SELECT * FROM {t}")
        backup[t] = [dict_from_row(r) for r in cursor.fetchall()]
    conn.close()

    backup['meta'] = {
        'app': 'QLTB - Quản lý thiết bị trường học',
        'export_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'version': '1.0'
    }

    response = Response(
        json.dumps(backup, ensure_ascii=False, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment;filename=qltb_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'}
    )
    return response

@app.route('/api/restore', methods=['POST'])
@admin_required
def restore_data():
    if 'file' not in request.files:
        return jsonify({'error': 'Chưa chọn tệp sao lưu JSON!'}), 400

    file = request.files['file']
    try:
        data = json.load(file)
    except Exception as e:
        return jsonify({'error': f'Lỗi đọc tệp JSON: {str(e)}'}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        tables = ['device_movements', 'borrow_requests', 'devices', 'users', 'locations', 'categories', 'activity_logs']
        for t in tables:
            cursor.execute(f"DELETE FROM {t}")

        for cat in data.get('categories', []):
            cursor.execute("INSERT INTO categories (id, name, icon) VALUES (?, ?, ?)", (cat.get('id'), cat.get('name'), cat.get('icon', 'package')))

        for loc in data.get('locations', []):
            cursor.execute("INSERT INTO locations (id, code, name, type, manager_name, description) VALUES (?, ?, ?, ?, ?, ?)",
                           (loc.get('id'), loc.get('code'), loc.get('name'), loc.get('type'), loc.get('manager_name'), loc.get('description')))

        for u in data.get('users', []):
            cursor.execute("INSERT INTO users (id, code, fullname, email, phone, role, department) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (u.get('id'), u.get('code'), u.get('fullname'), u.get('email'), u.get('phone'), u.get('role'), u.get('department')))

        for d in data.get('devices', []):
            cursor.execute("""
                INSERT INTO devices (id, code, name, category, current_location, status, price, purchase_date, supplier, specification, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (d.get('id'), d.get('code'), d.get('name'), d.get('category'), d.get('current_location'), d.get('status'), d.get('price'), d.get('purchase_date'), d.get('supplier'), d.get('specification'), d.get('notes')))

        for m in data.get('device_movements', []):
            cursor.execute("""
                INSERT INTO device_movements (id, device_id, device_code, device_name, from_location, to_location, moved_by, move_date, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (m.get('id'), m.get('device_id'), m.get('device_code'), m.get('device_name'), m.get('from_location'), m.get('to_location'), m.get('moved_by'), m.get('move_date'), m.get('reason')))

        for b in data.get('borrow_requests', []):
            cursor.execute("""
                INSERT INTO borrow_requests (id, request_code, user_code, user_name, department, device_code, device_name, borrow_date, expected_return_date, actual_return_date, purpose, status, return_condition, notes, approved_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (b.get('id'), b.get('request_code'), b.get('user_code'), b.get('user_name'), b.get('department'), b.get('device_code'), b.get('device_name'), b.get('borrow_date'), b.get('expected_return_date'), b.get('actual_return_date'), b.get('purpose'), b.get('status'), b.get('return_condition'), b.get('notes'), b.get('approved_by')))

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': f'Lỗi khôi phục: {str(e)}'}), 500

    conn.close()
    log_activity("Phục hồi dữ liệu", "Phục hồi thành công cơ sở dữ liệu từ file backup JSON", "system")
    return jsonify({'success': True, 'message': 'Đã phục hồi dữ liệu thành công!'})

@app.route('/api/reset-demo', methods=['POST'])
@admin_required
def reset_demo():
    try:
        from import_all_2022_data import run_import
        run_import()
        return jsonify({'success': True, 'message': 'Đã nạp lại toàn bộ dữ liệu thiết bị và phòng học chuẩn 2022 thành công!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("[*] HE THONG QUAN LY THIET BI TRUONG HOC (QLTB) DANG CHAY...")
    print("[*] Mo trinh duyet truy cap: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False)
