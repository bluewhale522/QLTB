import os
import shutil
import sqlite3
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'school_equipment.db')
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')

def create_full_backup():
    """
    Tự động sao lưu toàn bộ cơ sở dữ liệu:
    1. Sao chép snapshot file SQLite (.db)
    2. Xuất toàn bộ dữ liệu bảng ra file JSON độc lập (.json)
    """
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_backup_path = os.path.join(BACKUP_DIR, f"school_equipment_{timestamp}.db")
    json_backup_path = os.path.join(BACKUP_DIR, f"qltb_full_backup_{timestamp}.json")

    # 1. Snapshot file SQLite
    if os.path.exists(DB_PATH):
        # Dùng sqlite3 backup API để đảm bảo snapshot an toàn, không bị khóa (locked)
        src_conn = sqlite3.connect(DB_PATH)
        dst_conn = sqlite3.connect(db_backup_path)
        with dst_conn:
            src_conn.backup(dst_conn)
        src_conn.close()
        dst_conn.close()
        print(f"[BACKUP] Da tao snapshot database: {os.path.basename(db_backup_path)}")

    # 2. Xuất toàn bộ dữ liệu ra JSON
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        tables = ['users', 'locations', 'categories', 'devices', 'device_movements', 'borrow_requests', 'activity_logs', 'accounts']
        backup_data = {
            'meta': {
                'system': 'He thong Quan ly Thiet bi Truong hoc (QLTB)',
                'backup_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'version': '2.0-pro'
            }
        }

        total_records = 0
        for table in tables:
            try:
                cursor.execute(f"SELECT * FROM {table}")
                rows = [dict(r) for r in cursor.fetchall()]
                backup_data[table] = rows
                total_records += len(rows)
            except Exception as e:
                backup_data[table] = []

        conn.close()

        with open(json_backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)

        print(f"[BACKUP] Da xuat toan bo {total_records} ban ghi ra file JSON: {os.path.basename(json_backup_path)}")

    # Giữ lại tối đa 10 bản sao lưu gần nhất để không tốn dung lượng
    cleanup_old_backups(max_keep=10)

    return db_backup_path, json_backup_path

def cleanup_old_backups(max_keep=10):
    """Giữ lại tối đa max_keep bản sao lưu mới nhất"""
    try:
        files = [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if f.startswith('school_equipment_') or f.startswith('qltb_full_backup_')]
        files.sort(key=os.path.getmtime, reverse=True)
        # 2 files mỗi lần backup (.db và .json)
        max_files = max_keep * 2
        if len(files) > max_files:
            for f in files[max_files:]:
                try:
                    os.remove(f)
                except Exception:
                    pass
    except Exception:
        pass

if __name__ == '__main__':
    create_full_backup()
