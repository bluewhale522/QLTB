import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app
import sqlite3

client = app.test_client()

conn_init = sqlite3.connect('school_equipment.db')
conn_init.execute("DELETE FROM devices WHERE code = 'TB-TEST-001'")
conn_init.commit()
conn_init.close()

payload = {
    'code': 'TB-TEST-001',
    'name': 'Máy chiếu Panasonic PT-LB385',
    'category': 'Máy chiếu & Phông chiếu',
    'current_location': '1F18 - Lớp Moon (Mầm non)',
    'status': 'Đang sử dụng',
    'price': 15000000,
    'purchase_date': '2026-09-28',
    'supplier': 'Panasonic',
    'specification': '3800 ANSI Lumens',
    'notes': 'Test thêm thiết bị mới vào Lớp Moon'
}

res = client.post('/api/devices', json=payload)
print('POST /api/devices response:', res.status_code, res.get_json())

new_id = res.get_json()['id']
res_get = client.get(f'/api/devices/{new_id}')
print('GET device response:', res_get.status_code, res_get.get_json().get('current_location'))

# Test adding a location
loc_payload = {
    'code': '1F99',
    'name': '1F99 - Phòng Thí nghiệm Mầm non Mới',
    'type': 'Phòng chức năng & Bộ môn',
    'floor': 'Tầng 1',
    'manager_name': 'Cô Lan',
    'description': 'Phòng mới bổ sung'
}
res_loc = client.post('/api/locations', json=loc_payload)
print('POST /api/locations response:', res_loc.status_code, res_loc.get_json())

# Cleanup test records
conn = sqlite3.connect('school_equipment.db')
conn.execute("DELETE FROM devices WHERE code = 'TB-TEST-001'")
conn.execute("DELETE FROM locations WHERE code = '1F99'")
conn.commit()
conn.close()
print('Cleaned up test records successfully.')
