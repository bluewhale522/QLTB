import sqlite3
from datetime import datetime, timedelta
from database import get_db, init_db

def seed_database():
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    # Kiểm tra xem đã có dữ liệu chưa
    cursor.execute("SELECT COUNT(*) as count FROM devices")
    if cursor.fetchone()['count'] > 0:
        conn.close()
        return

    # 1. Danh mục thiết bị
    categories = [
        ("Máy tính & Thiết bị số", "monitor"),
        ("Máy chiếu & Trình chiếu", "projector"),
        ("Dụng cụ Thí nghiệm Khoa học", "flask-conical"),
        ("Dụng cụ Thể dục Thể thao", "trophy"),
        ("Âm thanh & Sự kiện", "mic"),
        ("Thiết bị Điện tử & Mạng", "wifi"),
        ("Thiết bị Văn phòng", "printer"),
        ("Dụng cụ Mỹ thuật & Âm nhạc", "palette")
    ]
    cursor.executemany("INSERT OR IGNORE INTO categories (name, icon) VALUES (?, ?)", categories)

    # 2. Vị trí & Phòng ban
    locations = [
        ("P-TIN1", "Phòng Tin học 01", "Phòng học", "Thầy Hoàng (Tin học)", "30 máy tính bộ cho học sinh"),
        ("P-TIN2", "Phòng Tin học 02", "Phòng học", "Cô Lan (Tin học)", "25 máy tính bộ và máy in"),
        ("P-HOA", "Phòng Thí nghiệm Hóa học", "Phòng thí nghiệm", "Thầy Nam (Hóa học)", "Tủ hút khí, hóa chất và dụng cụ thủy tinh"),
        ("P-LY", "Phòng Thí nghiệm Vật lý", "Phòng thí nghiệm", "Cô Mai (Vật lý)", "Bộ thí nghiệm quang học, điện từ"),
        ("P-SINH", "Phòng Thí nghiệm Sinh học", "Phòng thí nghiệm", "Thầy Đức (Sinh học)", "Kính hiển vi quang học, tiêu bản"),
        ("HT-A", "Hội trường Lớn (Nhà A)", "Hội trường", "Thầy Tuấn (Đoàn trường)", "Sức chứa 400 chỗ, hệ thống âm thanh ánh sáng"),
        ("SAN-TD", "Khu thể thao & Sân bóng", "Sân bãi", "Thầy Hùng (Thể dục)", "Sân bóng đá, bóng rổ, bóng chuyền"),
        ("KHO-TB", "Kho Thiết bị Trung tâm", "Kho", "Thầy Tuấn (Quản trị TB)", "Lưu trữ thiết bị dự phòng và chờ sửa"),
        ("VP-BGH", "Văn phòng Ban Giám hiệu", "Văn phòng", "Cô Hiệu trưởng", "Máy in, máy scan, laptop"),
        ("P-GV", "Phòng Chờ Giáo viên", "Văn phòng", "Cô Thảo (Công đoàn)", "Máy tính tra cứu, máy in giáo viên")
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO locations (code, name, type, manager_name, description) VALUES (?, ?, ?, ?, ?)",
        locations
    )

    # 3. Người dùng / Giáo viên
    users = [
        ("ADMIN01", "Nguyễn Văn Tuấn", "tuan.nv@truong.edu.vn", "0901234567", "admin", "Ban Quản trị Thiết bị"),
        ("GV001", "Trần Thị Mai", "mai.tt@truong.edu.vn", "0912345678", "teacher", "Tổ Tự nhiên (Vật lý)"),
        ("GV002", "Lê Văn Hoàng", "hoang.lv@truong.edu.vn", "0923456789", "teacher", "Tổ Toán - Tin học"),
        ("GV003", "Phạm Thị Lan", "lan.pt@truong.edu.vn", "0934567890", "teacher", "Tổ Toán - Tin học"),
        ("GV004", "Vũ Minh Nam", "nam.vm@truong.edu.vn", "0945678901", "teacher", "Tổ Tự nhiên (Hóa học)"),
        ("GV005", "Đặng Quang Hùng", "hung.dq@truong.edu.vn", "0956789012", "teacher", "Tổ Thể dục - Quốc phòng"),
        ("KT001", "Bùi Thế Anh", "theanh.kt@truong.edu.vn", "0967890123", "technician", "Tổ Kỹ thuật & Bảo trì")
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO users (code, fullname, email, phone, role, department) VALUES (?, ?, ?, ?, ?, ?)",
        users
    )

    # 4. Thiết bị trường học
    devices = [
        ("TB-PC-001", "Máy tính để bàn Dell OptiPlex 7090", "Máy tính & Thiết bị số", "Phòng Tin học 01", "Đang sử dụng", 14500000, "2024-08-15", "Công ty CP Tin học Sao Mai", "Core i5-11500, 16GB RAM, SSD 512GB, Màn hình 23.8 inch", "Trạm máy số 01"),
        ("TB-PC-002", "Máy tính để bàn Dell OptiPlex 7090", "Máy tính & Thiết bị số", "Phòng Tin học 01", "Đang sử dụng", 14500000, "2024-08-15", "Công ty CP Tin học Sao Mai", "Core i5-11500, 16GB RAM, SSD 512GB, Màn hình 23.8 inch", "Trạm máy số 02"),
        ("TB-PC-003", "Máy tính để bàn HP ProDesk 400 G7", "Máy tính & Thiết bị số", "Kho Thiết bị Trung tâm", "Sẵn sàng", 13200000, "2024-09-01", "Phong Vũ Computer", "Core i3-10100, 8GB RAM, SSD 256GB", "Máy dự phòng thay thế"),
        ("TB-LT-001", "Laptop giảng dạy Dell Vostro 3510", "Máy tính & Thiết bị số", "Kho Thiết bị Trung tâm", "Đang mượn", 15800000, "2025-01-10", "FPT Synnex", "Core i5, 16GB RAM, SSD 512GB, Pin 4 cell", "Thiết bị cấp mượn lưu động"),
        ("TB-MC-001", "Máy chiếu Sony VPL-EX435", "Máy chiếu & Trình chiếu", "Hội trường Lớn (Nhà A)", "Đang sử dụng", 18500000, "2023-11-20", "Công ty CP Nghe nhìn Á Châu", "Độ sáng 3200 Lumens, XGA 1024x768, HDMI/VGA", "Lắp cố định trần hội trường"),
        ("TB-MC-002", "Máy chiếu di động Epson EB-X06", "Máy chiếu & Trình chiếu", "Kho Thiết bị Trung tâm", "Đang mượn", 12900000, "2024-03-05", "Trần Anh Digital", "Độ sáng 3600 Lumens, HDMI, kèm túi đựng", "Máy chiếu phục vụ mượn phòng học"),
        ("TB-MC-003", "Máy chiếu Panasonic PT-LB386", "Máy chiếu & Trình chiếu", "Kho Thiết bị Trung tâm", "Hỏng", 16200000, "2023-05-12", "Trần Anh Digital", "Bóng chiếu bị chập chờn, mờ hình", "Chờ linh kiện bóng đèn thay thế"),
        ("TB-TN-001", "Kính hiển vi quang học 2 mắt Olympus CX23", "Dụng cụ Thí nghiệm Khoa học", "Phòng Thí nghiệm Sinh học", "Đang sử dụng", 22000000, "2024-02-18", "TBYT Đức Anh", "Độ phóng đại 40x - 1000x, Đèn LED", "Bảo quản trong tủ chống ẩm"),
        ("TB-TN-002", "Bộ thí nghiệm Quang học Laser trường học", "Dụng cụ Thí nghiệm Khoa học", "Kho Thiết bị Trung tâm", "Sẵn sàng", 6500000, "2024-10-05", "Công ty TB Giáo dục 1", "Nguồn Laser 3 tia, lăng kính, gương phản xạ", "Dụng cụ thí nghiệm khối 11"),
        ("TB-TN-003", "Bộ cân phân tích điện tử Sartorius Entris II", "Dụng cụ Thí nghiệm Khoa học", "Phòng Thí nghiệm Hóa học", "Đang sử dụng", 19500000, "2024-04-12", "Thiết bị Tân Cảng", "Độ chính xác 0.0001g, lồng kính chắn gió", "Phục vụ pha chế dung dịch"),
        ("TB-TT-001", "Bộ cột và lưới bóng chuyền tiêu chuẩn", "Dụng cụ Thể dục Thể thao", "Khu thể thao & Sân bóng", "Đang sử dụng", 5200000, "2024-05-10", "Động Lực Sport", "Trụ sắt mạ kẽm sơn tĩnh điện, lưới nylon", "Lắp đặt tại sân cỏ ngoài trời"),
        ("TB-TT-002", "Bộ 10 quả bóng đá số 5 Động Lực FIFA", "Dụng cụ Thể dục Thể thao", "Kho Thiết bị Trung tâm", "Sẵn sàng", 3800000, "2025-02-01", "Động Lực Sport", "Bóng da PU may tay chuyên nghiệp", "Phục vụ hội khỏe Phù Đổng"),
        ("TB-AT-001", "Bộ loa di động kéo tay kéo Mitsunal M35", "Âm thanh & Sự kiện", "Kho Thiết bị Trung tâm", "Sẵn sàng", 7200000, "2024-09-15", "Việt Hưng Audio", "Công suất 450W, kèm 2 micro không dây UHF", "Dùng cho chào cờ, ngoại khóa ngoài trời"),
        ("TB-AT-002", "Mixer bàn Yamaha MG12XU 12 kênh", "Âm thanh & Sự kiện", "Hội trường Lớn (Nhà A)", "Đang sử dụng", 11500000, "2023-11-20", "Việt Hưng Audio", "12 kênh ngõ vào, SPX Digital Multi Effects", "Tủ máy âm thanh sân khấu"),
        ("TB-IN-001", "Máy in Laser đa năng Canon MF241d", "Thiết bị Văn phòng", "Phòng Chờ Giáo viên", "Đang sử dụng", 6800000, "2024-01-20", "Lê Bảo Minh", "In 2 mặt tự động, Copy, Scan, 27 trang/phút", "Dành cho GV in giáo án và đề thi"),
        ("TB-WF-001", "Router Wifi chuyên dụng Aruba Instant On AP22", "Thiết bị Điện tử & Mạng", "Kho Thiết bị Trung tâm", "Bảo trì", 4200000, "2024-06-18", "Viễn thông Phương Nam", "Wifi 6 chuẩn AX1800, chịu tải 75 user", "Đang cập nhật Firmware và reset cấu hình")
    ]
    cursor.executemany(
        '''INSERT OR IGNORE INTO devices 
        (code, name, category, current_location, status, price, purchase_date, supplier, specification, notes) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        devices
    )

    # 5. Lịch sử di chuyển thiết bị mẫu
    now = datetime.now()
    cursor.execute("SELECT id FROM devices WHERE code = 'TB-LT-001'")
    lt_row = cursor.fetchone()
    lt_id = lt_row['id'] if lt_row else 1

    cursor.execute("SELECT id FROM devices WHERE code = 'TB-MC-002'")
    mc_row = cursor.fetchone()
    mc_id = mc_row['id'] if mc_row else 2

    movements = [
        (lt_id, "TB-LT-001", "Laptop giảng dạy Dell Vostro 3510", "Kho Thiết bị Trung tâm", "Phòng Tin học 01", "KT001", (now - timedelta(days=20)).strftime("%Y-%m-%d %H:%M:%S"), "Chuyển tạm thời để GV cài đặt phần mềm thi HSG"),
        (lt_id, "TB-LT-001", "Laptop giảng dạy Dell Vostro 3510", "Phòng Tin học 01", "Kho Thiết bị Trung tâm", "KT001", (now - timedelta(days=15)).strftime("%Y-%m-%d %H:%M:%S"), "Thu hồi về kho sau đợt thi HSG"),
        (mc_id, "TB-MC-002", "Máy chiếu di động Epson EB-X06", "Kho Thiết bị Trung tâm", "Phòng Chờ Giáo viên", "ADMIN01", (now - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S"), "Bố trí phục vụ họp hội đồng sư phạm"),
        (mc_id, "TB-MC-002", "Máy chiếu di động Epson EB-X06", "Phòng Chờ Giáo viên", "Kho Thiết bị Trung tâm", "ADMIN01", (now - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"), "Trả về kho bảo quản")
    ]
    cursor.executemany(
        '''INSERT INTO device_movements 
        (device_id, device_code, device_name, from_location, to_location, moved_by, move_date, reason) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        movements
    )

    # 6. Phiếu mượn - trả mẫu
    borrow_list = [
        (
            "PM-2026-001", "GV001", "Trần Thị Mai", "Tổ Tự nhiên (Vật lý)",
            "TB-LT-001", "Laptop giảng dạy Dell Vostro 3510",
            (now - timedelta(days=10)).strftime("%Y-%m-%d"),
            (now - timedelta(days=2)).strftime("%Y-%m-%d"), # Quá hạn 2 ngày!
            None, "Giảng dạy bài giảng điện tử và thao giảng cụm",
            "Đang mượn", "Tốt", "Cần gia hạn thêm nếu chưa xong", "ADMIN01"
        ),
        (
            "PM-2026-002", "GV004", "Vũ Minh Nam", "Tổ Tự nhiên (Hóa học)",
            "TB-MC-002", "Máy chiếu di động Epson EB-X06",
            (now - timedelta(days=1)).strftime("%Y-%m-%d"),
            (now + timedelta(days=3)).strftime("%Y-%m-%d"), # Còn hạn
            None, "Trình chiếu thí nghiệm mô phỏng Hóa 12",
            "Đang mượn", "Tốt", "Đã bàn giao đầy đủ cáp HDMI", "ADMIN01"
        ),
        (
            "PM-2026-003", "GV002", "Lê Văn Hoàng", "Tổ Toán - Tin học",
            "TB-TN-002", "Bộ thí nghiệm Quang học Laser trường học",
            (now - timedelta(days=7)).strftime("%Y-%m-%d"),
            (now - timedelta(days=3)).strftime("%Y-%m-%d"),
            (now - timedelta(days=3)).strftime("%Y-%m-%d"),
            "Thực hành giao thoa ánh sáng lớp 11A1",
            "Đã trả", "Tốt", "Đã hoàn trả nguyên hộp phụ kiện", "ADMIN01"
        ),
        (
            "PM-2026-004", "GV005", "Đặng Quang Hùng", "Tổ Thể dục - Quốc phòng",
            "TB-AT-001", "Bộ loa di động kéo tay kéo Mitsunal M35",
            now.strftime("%Y-%m-%d"),
            (now + timedelta(days=2)).strftime("%Y-%m-%d"),
            None, "Tập luyện văn nghệ cho lễ bế giảng",
            "Chờ duyệt", "Tốt", "Đăng ký mượn mới", None
        )
    ]
    cursor.executemany(
        '''INSERT INTO borrow_requests 
        (request_code, user_code, user_name, department, device_code, device_name, 
         borrow_date, expected_return_date, actual_return_date, purpose, status, return_condition, notes, approved_by) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        borrow_list
    )

    # 7. Hoạt động mẫu
    logs = [
        ("Nguyễn Văn Tuấn", "Khởi tạo hệ thống", "system", "Cài đặt và thiết lập cơ sở dữ liệu ban đầu cho trường học"),
        ("Nguyễn Văn Tuấn", "Duyệt phiếu mượn", "borrow", "Duyệt phiếu mượn PM-2026-001 cho GV Trần Thị Mai"),
        ("Bùi Thế Anh", "Di chuyển thiết bị", "device", "Di chuyển TB-LT-001 từ Kho Thiết bị sang Phòng Tin học 01"),
        ("Trần Thị Mai", "Tạo yêu cầu mượn", "borrow", "Tạo phiếu mượn PM-2026-001 mượn Laptop Dell")
    ]
    cursor.executemany(
        "INSERT INTO activity_logs (user_name, action, target_type, details) VALUES (?, ?, ?, ?)",
        logs
    )

    conn.commit()
    conn.close()
    print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()
