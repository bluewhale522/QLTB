import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'school_equipment.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Bảng người dùng / giáo viên
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        fullname TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        role TEXT NOT NULL DEFAULT 'teacher', -- 'admin', 'teacher', 'technician'
        department TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Bảng phòng ban / vị trí sử dụng
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        type TEXT DEFAULT 'Phòng học & Lớp học',
        floor TEXT DEFAULT 'Tầng 1',
        manager_name TEXT,
        description TEXT
    )
    ''')

    # Bảng danh mục thiết bị
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        icon TEXT DEFAULT 'package'
    )
    ''')

    # Bảng thiết bị
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        current_location TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Sẵn sàng', -- 'Sẵn sàng', 'Đang sử dụng', 'Đang mượn', 'Hỏng', 'Bảo trì', 'Đã thanh lý'
        price REAL DEFAULT 0,
        purchase_date TEXT,
        supplier TEXT,
        specification TEXT,
        notes TEXT,
        assigned_user TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Migration check for assigned_user column in devices
    cursor.execute("PRAGMA table_info(devices)")
    dev_cols = [r['name'] for r in cursor.fetchall()]
    if 'assigned_user' not in dev_cols:
        cursor.execute("ALTER TABLE devices ADD COLUMN assigned_user TEXT")

    # Migration check for account_id column in users
    cursor.execute("PRAGMA table_info(users)")
    usr_cols = [r['name'] for r in cursor.fetchall()]
    if 'account_id' not in usr_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN account_id INTEGER REFERENCES accounts(id)")


    # Bảng lịch sử di chuyển vị trí thiết bị
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS device_movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER NOT NULL,
        device_code TEXT NOT NULL,
        device_name TEXT NOT NULL,
        from_location TEXT NOT NULL,
        to_location TEXT NOT NULL,
        moved_by TEXT NOT NULL,
        move_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        reason TEXT NOT NULL,
        FOREIGN KEY(device_id) REFERENCES devices(id) ON DELETE CASCADE
    )
    ''')

    # Bảng mượn - trả thiết bị
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS borrow_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_code TEXT UNIQUE NOT NULL,
        user_code TEXT NOT NULL,
        user_name TEXT NOT NULL,
        department TEXT NOT NULL,
        device_code TEXT NOT NULL,
        device_name TEXT NOT NULL,
        borrow_date TEXT NOT NULL,
        expected_return_date TEXT NOT NULL,
        actual_return_date TEXT,
        purpose TEXT,
        status TEXT NOT NULL DEFAULT 'Chờ duyệt', -- 'Chờ duyệt', 'Đang mượn', 'Đã trả', 'Từ chối'
        return_condition TEXT DEFAULT 'Tốt',
        notes TEXT,
        approved_by TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Bảng nhật ký hoạt động hệ thống
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT,
        action TEXT NOT NULL,
        target_type TEXT,
        details TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Bảng tài khoản đăng nhập hệ thống (Phân quyền Admin & Guest)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        fullname TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'guest', -- 'admin', 'guest'
        email TEXT,
        phone TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Tạo tài khoản mặc định nếu chưa có
    cursor.execute("SELECT COUNT(*) as count FROM accounts")
    if cursor.fetchone()['count'] == 0:
        from werkzeug.security import generate_password_hash
        admin_pass = generate_password_hash('admin123')
        guest_pass = generate_password_hash('guest123')
        cursor.execute("""
            INSERT INTO accounts (username, password_hash, fullname, role, email, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('admin', admin_pass, 'Quản trị viên Hệ thống', 'admin', 'admin@truong.edu.vn', '0901234567'))
        cursor.execute("""
            INSERT INTO accounts (username, password_hash, fullname, role, email, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('guest', guest_pass, 'Khách vãng lai (Chỉ xem)', 'guest', 'guest@truong.edu.vn', '0900000000'))

    conn.commit()
    conn.close()

def log_activity(action, details, target_type='system', user_name='Quản trị viên'):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO activity_logs (user_name, action, target_type, details) VALUES (?, ?, ?, ?)",
            (user_name, action, target_type, details)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging activity: {e}")
