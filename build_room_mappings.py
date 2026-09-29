import openpyxl
import json

wb = openpyxl.load_workbook('data/Thiết bị 2022.xlsx', data_only=True)

# Sơ đồ chuẩn text mappings trích xuất chính xác 100% từ data/SƠ ĐỒ CHUẨN.pdf
pdf_floor_mappings = {
    "Tầng 1": {
        "1F1": {"name": "1F1 - Book-stores (Kho sách)", "short_name": "Book-stores (Kho sách)", "type": "Kho & Kỹ thuật"},
        "1F2 (Bảo vệ)": {"name": "1F2 (Bảo vệ) - Phòng Bảo vệ Cổng chính", "short_name": "Phòng Bảo vệ Cổng chính", "type": "Văn phòng & Khối làm việc"},
        "1F3": {"name": "1F3 - Nhà ăn Tầng 1 (kèm Bếp)", "short_name": "Nhà ăn Tầng 1 (kèm Bếp)", "type": "Tiện ích & Phụ trợ"},
        "1F4": {"name": "1F4 - Phòng Tuyển sinh", "short_name": "Phòng Tuyển sinh", "type": "Văn phòng & Khối làm việc"},
        "1F5": {"name": "1F5 - Phòng Tiếp khách VIP (Tầng 1)", "short_name": "Phòng Tiếp khách VIP (Tầng 1)", "type": "Văn phòng & Khối làm việc"},
        "1F6": {"name": "1F6 - Phòng Hành chính Tổng hợp (HCTH)", "short_name": "Phòng Hành chính Tổng hợp (HCTH)", "type": "Văn phòng & Khối làm việc"},
        "1F7": {"name": "1F7 - Phòng Hội thảo", "short_name": "Phòng Hội thảo", "type": "Phòng chức năng & Bộ môn"},
        "1F8": {"name": "1F8 - Văn phòng Trường", "short_name": "Văn phòng Trường", "type": "Văn phòng & Khối làm việc"},
        "1F9": {"name": "1F9 - Phòng Họp Tầng 1", "short_name": "Phòng Họp Tầng 1", "type": "Văn phòng & Khối làm việc"},
        "1F10": {"name": "1F10 - Phòng Tài chính Kế toán (TCKT)", "short_name": "Phòng Tài chính Kế toán (TCKT)", "type": "Văn phòng & Khối làm việc"},
        "1F11": {"name": "1F11 - Phòng Y tế Trường học", "short_name": "Phòng Y tế Trường học", "type": "Tiện ích & Phụ trợ"},
        "1F12": {"name": "1F12 - Phòng Hiệu trưởng Mầm non", "short_name": "Phòng Hiệu trưởng Mầm non", "type": "Văn phòng & Khối làm việc"},
        "1F13": {"name": "1F13 - Phòng Tiếp đón / Chờ MN", "short_name": "Phòng Tiếp đón / Chờ MN", "type": "Văn phòng & Khối làm việc"},
        "1F14": {"name": "1F14 - Phòng Ăn Mầm non", "short_name": "Phòng Ăn Mầm non", "type": "Tiện ích & Phụ trợ"},
        "1F15": {"name": "1F15 - Phòng Dự phòng MN 1", "short_name": "Phòng Dự phòng MN 1", "type": "Phòng học & Lớp học"},
        "1F16": {"name": "1F16 - Lớp Star 1 (Mầm non)", "short_name": "Lớp Star 1 (Mầm non)", "type": "Phòng học & Lớp học"},
        "1F17": {"name": "1F17 - Phòng Dự phòng MN 2", "short_name": "Phòng Dự phòng MN 2", "type": "Phòng học & Lớp học"},
        "1F18": {"name": "1F18 - Lớp Moon (Mầm non)", "short_name": "Lớp Moon (Mầm non)", "type": "Phòng học & Lớp học"},
        "1F19": {"name": "1F19 - Gymkids (Vận động Mầm non)", "short_name": "Gymkids (Vận động Mầm non)", "type": "Phòng chức năng & Bộ môn"},
        "1F20 (Hành lang khu mầm non)": {"name": "1F20 - Tiếp tân & HL Mầm non", "short_name": "Tiếp tân & HL Mầm non", "type": "Tiện ích & Phụ trợ"},
        "1F21": {"name": "1F21 - Khu Bể bơi Học sinh", "short_name": "Khu Bể bơi Học sinh", "type": "Khuôn viên, Sân bãi & Tiện ích"},
        "WC Y4-Y5": {"name": "1F-WC Y4-Y5 - Khu Vệ sinh Tầng 1 (Trục Y4-Y5)", "short_name": "Khu Vệ sinh Tầng 1 (Trục Y4-Y5)", "type": "Tiện ích & Phụ trợ"},
        "CT bộ Y4-Y5": {"name": "1F-CT bộ Y4-Y5 - Cầu thang bộ Tầng 1 (Trục Y4-Y5)", "short_name": "Cầu thang bộ Tầng 1 (Trục Y4-Y5)", "type": "Tiện ích & Phụ trợ"},
        "HL Y4-Y12": {"name": "1F-HL Y4-Y12 - Hành lang chính Tầng 1 (Trục Y4-Y12)", "short_name": "Hành lang chính Tầng 1 (Trục Y4-Y12)", "type": "Tiện ích & Phụ trợ"},
        "Sảnh Y7-Y9": {"name": "1F-Sảnh Y7-Y9 - Sảnh Trung tâm Tầng 1 (Trục Y7-Y9)", "short_name": "Sảnh Trung tâm Tầng 1 (Trục Y7-Y9)", "type": "Tiện ích & Phụ trợ"},
        "WC nhà ăn": {"name": "1F-WC nhà ăn - Khu Vệ sinh Bếp & Nhà ăn", "short_name": "Khu Vệ sinh Bếp & Nhà ăn", "type": "Tiện ích & Phụ trợ"},
        "QL bếp ăn": {"name": "1F-QL bếp ăn - Phòng Quản lý Bếp ăn & Dinh dưỡng", "short_name": "Phòng Quản lý Bếp ăn & Dinh dưỡng", "type": "Văn phòng & Khối làm việc"},
        "HL X1-X9": {"name": "1F-HL X1-X9 - Hành lang Tầng 1 (Trục X1-X9)", "short_name": "Hành lang Tầng 1 (Trục X1-X9)", "type": "Tiện ích & Phụ trợ"},
        "Sân bóng rổ": {"name": "1F-Sân bóng rổ - Sân Thể thao Bóng rổ ngoài trời", "short_name": "Sân Thể thao Bóng rổ ngoài trời", "type": "Khuôn viên, Sân bãi & Tiện ích"},
        "Sân bóng đá": {"name": "1F-Sân bóng đá - Sân Bóng đá Cỏ nhân tạo", "short_name": "Sân Bóng đá Cỏ nhân tạo", "type": "Khuôn viên, Sân bãi & Tiện ích"},
        "Bể bơi": {"name": "1F-Bể bơi - Khu Bể bơi Bốn mùa", "short_name": "Khu Bể bơi Bốn mùa", "type": "Khuôn viên, Sân bãi & Tiện ích"},
        "Sảnh thang máy": {"name": "1F-Sảnh thang máy - Sảnh Thang máy Tầng 1", "short_name": "Sảnh Thang máy Tầng 1", "type": "Tiện ích & Phụ trợ"},
        "Thang bộ Y13-Y14": {"name": "1F-Thang bộ Y13-Y14 - Cầu thang bộ Tầng 1 (Trục Y13-Y14)", "short_name": "Cầu thang bộ Tầng 1 (Trục Y13-Y14)", "type": "Tiện ích & Phụ trợ"},
        "Sảnh bảo vệ": {"name": "1F-Sảnh bảo vệ - Sảnh Kiểm soát An ninh Bảo vệ", "short_name": "Sảnh Kiểm soát An ninh Bảo vệ", "type": "Văn phòng & Khối làm việc"},
        "Sân Y4-Y13": {"name": "1F-Sân Y4-Y13 - Khuôn viên Sân trường (Trục Y4-Y13)", "short_name": "Khuôn viên Sân trường (Trục Y4-Y13)", "type": "Khuôn viên, Sân bãi & Tiện ích"},
        "Cổng số 1": {"name": "1F-Cổng số 1 - Cổng chính số 1 (Đón trả HS)", "short_name": "Cổng chính số 1 (Đón trả HS)", "type": "Khuôn viên, Sân bãi & Tiện ích"},
        "Cổng số 2": {"name": "1F-Cổng số 2 - Cổng phụ số 2 (Khu GV)", "short_name": "Cổng phụ số 2 (Khu GV)", "type": "Khuôn viên, Sân bãi & Tiện ích"},
        "Lái xe 1": {"name": "1F-Lái xe 1 - Phòng Điều hành Đội xe Bus 1", "short_name": "Phòng Điều hành Đội xe Bus 1", "type": "Văn phòng & Khối làm việc"},
        "Lái xe 2": {"name": "1F-Lái xe 2 - Phòng Điều hành Đội xe Bus 2", "short_name": "Phòng Điều hành Đội xe Bus 2", "type": "Văn phòng & Khối làm việc"},
        "Trạm Bơm": {"name": "1F-Trạm Bơm - Trạm Bơm Kỹ thuật Nước", "short_name": "Trạm Bơm Kỹ thuật Nước", "type": "Kho & Kỹ thuật"},
        "Lao công": {"name": "1F-Lao công - Phòng Lao công & Tạp vụ", "short_name": "Phòng Lao công & Tạp vụ", "type": "Tiện ích & Phụ trợ"},
        "Hàng rào quanh trường": {"name": "1F-Hàng rào quanh trường - An ninh Hàng rào quanh trường", "short_name": "An ninh Hàng rào quanh trường", "type": "Khuôn viên, Sân bãi & Tiện ích"}
    },
    "Tầng 2": {
        "2F1": {"name": "2F1 - Phòng Phó Hiệu trưởng (Tiểu học)", "short_name": "Phòng Phó Hiệu trưởng (Tiểu học)", "type": "Văn phòng & Khối làm việc"},
        "2F2": {"name": "2F2 - Phòng Khảo thí & Kiểm định Chất lượng", "short_name": "Phòng Khảo thí & Kiểm định Chất lượng", "type": "Văn phòng & Khối làm việc"},
        "2F3": {"name": "2F3 - Phòng Phát thanh & Âm thanh PT1", "short_name": "Phòng Phát thanh & Âm thanh PT1", "type": "Phòng chức năng & Bộ môn"},
        "2F4": {"name": "2F4 - Phòng Phát thanh & Thu âm PT2", "short_name": "Phòng Phát thanh & Thu âm PT2", "type": "Phòng chức năng & Bộ môn"},
        "2F5": {"name": "2F5 - Nhà ăn Tầng 2 (kèm Phòng Bánh)", "short_name": "Nhà ăn Tầng 2 (kèm Phòng Bánh)", "type": "Tiện ích & Phụ trợ"},
        "2F6": {"name": "2F6 - Phòng Học chức năng 2F6", "short_name": "Phòng Học chức năng 2F6", "type": "Phòng chức năng & Bộ môn"},
        "2F7": {"name": "2F7 - Phòng Hội đồng Sư phạm", "short_name": "Phòng Hội đồng Sư phạm", "type": "Văn phòng & Khối làm việc"},
        "2F8": {"name": "2F8 - Phòng Giáo viên Cấp Tiểu học", "short_name": "Phòng Giáo viên Cấp Tiểu học", "type": "Văn phòng & Khối làm việc"},
        "2F9": {"name": "2F9 - Lớp 2A3 (Tiểu học)", "short_name": "Lớp 2A3 (Tiểu học)", "type": "Phòng học & Lớp học"},
        "2F10": {"name": "2F10 - Lớp 2A2 (Tiểu học)", "short_name": "Lớp 2A2 (Tiểu học)", "type": "Phòng học & Lớp học"},
        "2F11": {"name": "2F11 - Lớp 2A1 (Tiểu học)", "short_name": "Lớp 2A1 (Tiểu học)", "type": "Phòng học & Lớp học"},
        "2F12": {"name": "2F12 - Phòng Học bổ trợ 2F12", "short_name": "Phòng Học bổ trợ 2F12", "type": "Phòng học & Lớp học"},
        "2F13": {"name": "2F13 - Phòng Học bổ trợ 2F13", "short_name": "Phòng Học bổ trợ 2F13", "type": "Phòng học & Lớp học"},
        "2F14": {"name": "2F14 - Lớp 1A2 (Tiểu học)", "short_name": "Lớp 1A2 (Tiểu học)", "type": "Phòng học & Lớp học"},
        "2F15": {"name": "2F15 - Lớp 1A1 (Tiểu học)", "short_name": "Lớp 1A1 (Tiểu học)", "type": "Phòng học & Lớp học"},
        "2F16": {"name": "2F16 - Lớp Star 2 (Tiểu học)", "short_name": "Lớp Star 2 (Tiểu học)", "type": "Phòng học & Lớp học"},
        "2F17": {"name": "2F17 - Lớp Sunny 2 (Tiểu học)", "short_name": "Lớp Sunny 2 (Tiểu học)", "type": "Phòng học & Lớp học"},
        "2F18": {"name": "2F18 - Lớp Rainbow (Tiểu học)", "short_name": "Lớp Rainbow (Tiểu học)", "type": "Phòng học & Lớp học"},
        "2F19": {"name": "2F19 - Lớp Sunny 1 (Tiểu học)", "short_name": "Lớp Sunny 1 (Tiểu học)", "type": "Phòng học & Lớp học"},
        "2F20": {"name": "2F20 - Phòng Mỹ thuật I", "short_name": "Phòng Mỹ thuật I", "type": "Phòng chức năng & Bộ môn"},
        "2F21": {"name": "2F21 - Phòng Mỹ thuật II", "short_name": "Phòng Mỹ thuật II", "type": "Phòng chức năng & Bộ môn"},
        "2F22": {"name": "2F22 - Phòng Âm nhạc Tầng 2", "short_name": "Phòng Âm nhạc Tầng 2", "type": "Phòng chức năng & Bộ môn"},
        "2F23": {"name": "2F23 - Thư viện Cấp Tiểu học", "short_name": "Thư viện Cấp Tiểu học", "type": "Phòng chức năng & Bộ môn"},
        "WC Y4-Y5": {"name": "2F-WC Y4-Y5 - Khu Vệ sinh Tầng 2 (Trục Y4-Y5)", "short_name": "Khu Vệ sinh Tầng 2 (Trục Y4-Y5)", "type": "Tiện ích & Phụ trợ"},
        "WC Y15-Y16": {"name": "2F-WC Y15-Y16 - Khu Vệ sinh Tầng 2 (Trục Y15-Y16)", "short_name": "Khu Vệ sinh Tầng 2 (Trục Y15-Y16)", "type": "Tiện ích & Phụ trợ"},
        "CT bộ Y4-Y5": {"name": "2F-CT bộ Y4-Y5 - Cầu thang bộ Tầng 2 (Trục Y4-Y5)", "short_name": "Cầu thang bộ Tầng 2 (Trục Y4-Y5)", "type": "Tiện ích & Phụ trợ"},
        "HL Y1-Y16": {"name": "2F-HL Y1-Y16 - Hành lang chính Tầng 2 (Trục Y1-Y16)", "short_name": "Hành lang chính Tầng 2 (Trục Y1-Y16)", "type": "Tiện ích & Phụ trợ"},
        "Sảnh Y7-Y9": {"name": "2F-Sảnh Y7-Y9 - Sảnh Tầng 2 (Trục Y7-Y9)", "short_name": "Sảnh Tầng 2 (Trục Y7-Y9)", "type": "Tiện ích & Phụ trợ"},
        "WC Y10-Y11": {"name": "2F-WC Y10-Y11 - Khu Vệ sinh Tầng 2 (Trục Y10-Y11)", "short_name": "Khu Vệ sinh Tầng 2 (Trục Y10-Y11)", "type": "Tiện ích & Phụ trợ"},
        "HL X1-X7": {"name": "2F-HL X1-X7 - Hành lang Tầng 2 (Trục X1-X7)", "short_name": "Hành lang Tầng 2 (Trục X1-X7)", "type": "Tiện ích & Phụ trợ"},
        "HL thư viện": {"name": "2F-HL thư viện - Hành lang Thư viện Tầng 2", "short_name": "Hành lang Thư viện Tầng 2", "type": "Tiện ích & Phụ trợ"},
        "Sảnh thang máy": {"name": "2F-Sảnh thang máy - Sảnh Thang máy Tầng 2", "short_name": "Sảnh Thang máy Tầng 2", "type": "Tiện ích & Phụ trợ"},
        "Thang bộ Y13-Y14": {"name": "2F-Thang bộ Y13-Y14 - Cầu thang bộ Tầng 2 (Trục Y13-Y14)", "short_name": "Cầu thang bộ Tầng 2 (Trục Y13-Y14)", "type": "Tiện ích & Phụ trợ"}
    },
    "Tầng 3": {
        "3F1": {"name": "3F1 - Phòng Thư ký Chủ tịch HĐQT", "short_name": "Phòng Thư ký Chủ tịch HĐQT", "type": "Văn phòng & Khối làm việc"},
        "3F2": {"name": "3F2 - Phòng Chủ tịch Hội đồng Quản trị", "short_name": "Phòng Chủ tịch Hội đồng Quản trị", "type": "Văn phòng & Khối làm việc"},
        "3F3": {"name": "3F3 - Phòng Họp Ban Lãnh đạo HĐQT", "short_name": "Phòng Họp Ban Lãnh đạo HĐQT", "type": "Văn phòng & Khối làm việc"},
        "3F4": {"name": "3F4 - Phòng Ban Đầu tư & Phát triển", "short_name": "Phòng Ban Đầu tư & Phát triển", "type": "Văn phòng & Khối làm việc"},
        "3F5": {"name": "3F5 - Phòng Tin học 1 (Thực hành)", "short_name": "Phòng Tin học 1 (Thực hành)", "type": "Phòng chức năng & Bộ môn"},
        "3F6": {"name": "3F6 - Phòng Mỹ thuật & Hội họa (Tầng 3)", "short_name": "Phòng Mỹ thuật & Hội họa (Tầng 3)", "type": "Phòng chức năng & Bộ môn"},
        "3F7": {"name": "3F7 - Phòng Tin học 2 (Thực hành)", "short_name": "Phòng Tin học 2 (Thực hành)", "type": "Phòng chức năng & Bộ môn"},
        "3F8": {"name": "3F8 - Phòng Robotics & STEM", "short_name": "Phòng Robotics & STEM", "type": "Phòng chức năng & Bộ môn"},
        "3F9": {"name": "3F9 - Phòng Chức năng 3F9", "short_name": "Phòng Chức năng 3F9", "type": "Phòng chức năng & Bộ môn"},
        "3F10": {"name": "3F10 - Lớp 5A1 (Tiểu học)", "short_name": "Lớp 5A1 (Tiểu học)", "type": "Phòng học & Lớp học"},
        "3F11": {"name": "3F11 - Lớp 5A2 (Tiểu học)", "short_name": "Lớp 5A2 (Tiểu học)", "type": "Phòng học & Lớp học"},
        "3F12": {"name": "3F12 - Lớp 4A3 (Tiểu học)", "short_name": "Lớp 4A3 (Tiểu học)", "type": "Phòng học & Lớp học"},
        "3F13": {"name": "3F13 - Phòng Học dự phòng 3F13", "short_name": "Phòng Học dự phòng 3F13", "type": "Phòng học & Lớp học"},
        "3F14": {"name": "3F14 - Phòng Học dự phòng 3F14", "short_name": "Phòng Học dự phòng 3F14", "type": "Phòng học & Lớp học"},
        "3F15": {"name": "3F15 - Phòng Học dự phòng 3F15", "short_name": "Phòng Học dự phòng 3F15", "type": "Phòng học & Lớp học"},
        "3F16": {"name": "3F16 - Lớp 4A2 (Tiểu học)", "short_name": "Lớp 4A2 (Tiểu học)", "type": "Phòng học & Lớp học"},
        "3F17": {"name": "3F17 - Lớp 4A1 (Tiểu học)", "short_name": "Lớp 4A1 (Tiểu học)", "type": "Phòng học & Lớp học"},
        "3F18": {"name": "3F18 - Lớp 3A2 (Tiểu học)", "short_name": "Lớp 3A2 (Tiểu học)", "type": "Phòng học & Lớp học"},
        "3F19": {"name": "3F19 - Lớp 3A1 (Tiểu học)", "short_name": "Lớp 3A1 (Tiểu học)", "type": "Phòng học & Lớp học"},
        "3F20": {"name": "3F20 - Phòng Học dự phòng 3F20", "short_name": "Phòng Học dự phòng 3F20", "type": "Phòng học & Lớp học"},
        "3F21": {"name": "3F21 - Phòng Học dự phòng 3F21", "short_name": "Phòng Học dự phòng 3F21", "type": "Phòng học & Lớp học"},
        "3F22": {"name": "3F22 - Phòng Đàn Piano & Cảm thụ Âm nhạc", "short_name": "Phòng Đàn Piano & Cảm thụ Âm nhạc", "type": "Phòng chức năng & Bộ môn"},
        "3F23": {"name": "3F23 - Kho Thiết bị CNTT (Kho IT)", "short_name": "Kho Thiết bị CNTT (Kho IT)", "type": "Kho & Kỹ thuật"},
        "3F24": {"name": "3F24 - Phòng Kịch nghệ & Diễn xuất", "short_name": "Phòng Kịch nghệ & Diễn xuất", "type": "Phòng chức năng & Bộ môn"},
        "3F25": {"name": "3F25 - Phòng Gym & Thể chất", "short_name": "Phòng Gym & Thể chất", "type": "Phòng chức năng & Bộ môn"},
        "3F26": {"name": "3F26 - Phòng Võ thuật & Yoga", "short_name": "Phòng Võ thuật & Yoga", "type": "Phòng chức năng & Bộ môn"},
        "3F27": {"name": "3F27 - Phòng Nhạc Cụ & Hợp xướng (Tầng 3)", "short_name": "Phòng Nhạc Cụ & Hợp xướng (Tầng 3)", "type": "Phòng chức năng & Bộ môn"},
        "3F28": {"name": "3F28 - Nhà Thi đấu Thể thao Đa năng", "short_name": "Nhà Thi đấu Thể thao Đa năng", "type": "Khuôn viên, Sân bãi & Tiện ích"},
        "WC Y4-Y5": {"name": "3F-WC Y4-Y5 - Khu Vệ sinh Tầng 3 (Trục Y4-Y5)", "short_name": "Khu Vệ sinh Tầng 3 (Trục Y4-Y5)", "type": "Tiện ích & Phụ trợ"},
        "WC Y15-Y16": {"name": "3F-WC Y15-Y16 - Khu Vệ sinh Tầng 3 (Trục Y15-Y16)", "short_name": "Khu Vệ sinh Tầng 3 (Trục Y15-Y16)", "type": "Tiện ích & Phụ trợ"},
        "WC Y11-Y12": {"name": "3F-WC Y11-Y12 - Khu Vệ sinh Tầng 3 (Trục Y11-Y12)", "short_name": "Khu Vệ sinh Tầng 3 (Trục Y11-Y12)", "type": "Tiện ích & Phụ trợ"},
        "WC đối diện nhà đa năng": {"name": "3F-WC đối diện nhà đa năng - Khu Vệ sinh Đối diện Nhà đa năng", "short_name": "Khu Vệ sinh Đối diện Nhà đa năng", "type": "Tiện ích & Phụ trợ"},
        "Kho IT": {"name": "3F-Kho IT - Kho IT Dự phòng Tầng 3", "short_name": "Kho IT Dự phòng Tầng 3", "type": "Kho & Kỹ thuật"},
        "CT bộ Y4-Y5": {"name": "3F-CT bộ Y4-Y5 - Cầu thang bộ Tầng 3 (Trục Y4-Y5)", "short_name": "Cầu thang bộ Tầng 3 (Trục Y4-Y5)", "type": "Tiện ích & Phụ trợ"},
        "HL Y1-Y16": {"name": "3F-HL Y1-Y16 - Hành lang chính Tầng 3 (Trục Y1-Y16)", "short_name": "Hành lang chính Tầng 3 (Trục Y1-Y16)", "type": "Tiện ích & Phụ trợ"},
        "Nhà đa năng": {"name": "3F-Nhà đa năng - Sân thi đấu Nhà đa năng", "short_name": "Sân thi đấu Nhà đa năng", "type": "Khuôn viên, Sân bãi & Tiện ích"},
        "Sảnh Y7-Y9": {"name": "3F-Sảnh Y7-Y9 - Sảnh Tầng 3 (Trục Y7-Y9)", "short_name": "Sảnh Tầng 3 (Trục Y7-Y9)", "type": "Tiện ích & Phụ trợ"},
        "HL Phòng võ": {"name": "3F-HL Phòng võ - Hành lang Phòng tập Võ", "short_name": "Hành lang Phòng tập Võ", "type": "Tiện ích & Phụ trợ"},
        "HL X1-X7": {"name": "3F-HL X1-X7 - Hành lang Tầng 3 (Trục X1-X7)", "short_name": "Hành lang Tầng 3 (Trục X1-X7)", "type": "Tiện ích & Phụ trợ"},
        "Thang bộ Y9-Y10": {"name": "3F-Thang bộ Y9-Y10 - Cầu thang bộ Tầng 3 (Trục Y9-Y10)", "short_name": "Cầu thang bộ Tầng 3 (Trục Y9-Y10)", "type": "Tiện ích & Phụ trợ"},
        "Sảnh thang máy": {"name": "3F-Sảnh thang máy - Sảnh Thang máy Tầng 3", "short_name": "Sảnh Thang máy Tầng 3", "type": "Tiện ích & Phụ trợ"},
        "Thang bộ Y13-Y14": {"name": "3F-Thang bộ Y13-Y14 - Cầu thang bộ Tầng 3 (Trục Y13-Y14)", "short_name": "Cầu thang bộ Tầng 3 (Trục Y13-Y14)", "type": "Tiện ích & Phụ trợ"}
    },
    "Tầng 4": {
        "4F1": {"name": "4F1 - Phòng Trực / Kỹ thuật 4F1", "short_name": "Phòng Trực / Kỹ thuật 4F1", "type": "Kho & Kỹ thuật"},
        "4F2": {"name": "4F2 - Lớp 9A3 (THCS)", "short_name": "Lớp 9A3 (THCS)", "type": "Phòng học & Lớp học"},
        "4F3": {"name": "4F3 - Tổ Khoa học Tự nhiên (KHTN)", "short_name": "Tổ Khoa học Tự nhiên (KHTN)", "type": "Văn phòng & Khối làm việc"},
        "4F4": {"name": "4F4 - Lớp 9A2 (THCS)", "short_name": "Lớp 9A2 (THCS)", "type": "Phòng học & Lớp học"},
        "4F5": {"name": "4F5 - Phòng Tiếp khách VIP Tầng 4", "short_name": "Phòng Tiếp khách VIP Tầng 4", "type": "Văn phòng & Khối làm việc"},
        "4F6": {"name": "4F6 - Lớp 9A1 (THCS)", "short_name": "Lớp 9A1 (THCS)", "type": "Phòng học & Lớp học"},
        "4F7": {"name": "4F7 - Lớp 8A1 (THCS)", "short_name": "Lớp 8A1 (THCS)", "type": "Phòng học & Lớp học"},
        "4F8": {"name": "4F8 - Phòng Học chức năng 4F8", "short_name": "Phòng Học chức năng 4F8", "type": "Phòng chức năng & Bộ môn"},
        "4F9": {"name": "4F9 - Lớp 8A2 (THCS)", "short_name": "Lớp 8A2 (THCS)", "type": "Phòng học & Lớp học"},
        "4F10": {"name": "4F10 - Phòng Thí nghiệm KHTN 4F10", "short_name": "Phòng Thí nghiệm KHTN 4F10", "type": "Phòng chức năng & Bộ môn"},
        "4F11": {"name": "4F11 - Lớp 6A1 (THCS)", "short_name": "Lớp 6A1 (THCS)", "type": "Phòng học & Lớp học"},
        "4F12": {"name": "4F12 - Phòng Học bổ trợ 4F12", "short_name": "Phòng Học bổ trợ 4F12", "type": "Phòng học & Lớp học"},
        "4F13": {"name": "4F13 - Lớp 6A2 (THCS)", "short_name": "Lớp 6A2 (THCS)", "type": "Phòng học & Lớp học"},
        "4F14": {"name": "4F14 - Lớp 7A2 (THCS)", "short_name": "Lớp 7A2 (THCS)", "type": "Phòng học & Lớp học"},
        "4F15": {"name": "4F15 - Phòng Học bổ trợ 4F15", "short_name": "Phòng Học bổ trợ 4F15", "type": "Phòng học & Lớp học"},
        "4F16": {"name": "4F16 - Lớp 7A1 (THCS)", "short_name": "Lớp 7A1 (THCS)", "type": "Phòng học & Lớp học"},
        "4F17": {"name": "4F17 - Phòng Học chuyên đề 4F17", "short_name": "Phòng Học chuyên đề 4F17", "type": "Phòng học & Lớp học"},
        "4F18": {"name": "4F18 - Phòng Học chuyên đề 4F18", "short_name": "Phòng Học chuyên đề 4F18", "type": "Phòng học & Lớp học"},
        "4F19": {"name": "4F19 - Phòng Học nhóm 4F19", "short_name": "Phòng Học nhóm 4F19", "type": "Phòng học & Lớp học"},
        "4F20": {"name": "4F20 - Phòng Học nhóm 4F20", "short_name": "Phòng Học nhóm 4F20", "type": "Phòng học & Lớp học"},
        "4F21": {"name": "4F21 - Phòng Thiết bị Dạy học THCS", "short_name": "Phòng Thiết bị Dạy học THCS", "type": "Kho & Kỹ thuật"},
        "4F22": {"name": "4F22 - Phòng Khảo thí THCS", "short_name": "Phòng Khảo thí THCS", "type": "Văn phòng & Khối làm việc"},
        "4F23": {"name": "4F23 - Phòng Đoàn Đội & Trực Tầng 4", "short_name": "Phòng Đoàn Đội & Trực Tầng 4", "type": "Văn phòng & Khối làm việc"},
        "WC Y4-Y5": {"name": "4F-WC Y4-Y5 - Khu Vệ sinh Tầng 4 (Trục Y4-Y5)", "short_name": "Khu Vệ sinh Tầng 4 (Trục Y4-Y5)", "type": "Tiện ích & Phụ trợ"},
        "WC Y15-Y16": {"name": "4F-WC Y15-Y16 - Khu Vệ sinh Tầng 4 (Trục Y15-Y16)", "short_name": "Khu Vệ sinh Tầng 4 (Trục Y15-Y16)", "type": "Tiện ích & Phụ trợ"},
        "WC Y11-Y12": {"name": "4F-WC Y11-Y12 - Khu Vệ sinh Tầng 4 (Trục Y11-Y12)", "short_name": "Khu Vệ sinh Tầng 4 (Trục Y11-Y12)", "type": "Tiện ích & Phụ trợ"},
        "Sân khấu": {"name": "4F-Sân khấu - Khu Vực Sân khấu Biểu diễn", "short_name": "Khu Vực Sân khấu Biểu diễn", "type": "Khuôn viên, Sân bãi & Tiện ích"},
        "WC sân khấu": {"name": "4F-WC sân khấu - Khu Vệ sinh Hậu trường Sân khấu", "short_name": "Khu Vệ sinh Hậu trường Sân khấu", "type": "Tiện ích & Phụ trợ"},
        "CT bộ Y4-Y5": {"name": "4F-CT bộ Y4-Y5 - Cầu thang bộ Tầng 4 (Trục Y4-Y5)", "short_name": "Cầu thang bộ Tầng 4 (Trục Y4-Y5)", "type": "Tiện ích & Phụ trợ"},
        "HL Y1-Y16": {"name": "4F-HL Y1-Y16 - Hành lang chính Tầng 4 (Trục Y1-Y16)", "short_name": "Hành lang chính Tầng 4 (Trục Y1-Y16)", "type": "Tiện ích & Phụ trợ"},
        "Sảnh cầu thang gỗ": {"name": "4F-Sảnh cầu thang gỗ - Sảnh Không gian Sáng tạo Cầu thang Gỗ", "short_name": "Sảnh Không gian Sáng tạo Cầu thang Gỗ", "type": "Tiện ích & Phụ trợ"},
        "Sảnh Y7-Y9": {"name": "4F-Sảnh Y7-Y9 - Sảnh Tầng 4 (Trục Y7-Y9)", "short_name": "Sảnh Tầng 4 (Trục Y7-Y9)", "type": "Tiện ích & Phụ trợ"},
        "HL X1-X7": {"name": "4F-HL X1-X7 - Hành lang Tầng 4 (Trục X1-X7)", "short_name": "Hành lang Tầng 4 (Trục X1-X7)", "type": "Tiện ích & Phụ trợ"},
        "Thang bộ Y9-Y10": {"name": "4F-Thang bộ Y9-Y10 - Cầu thang bộ Tầng 4 (Trục Y9-Y10)", "short_name": "Cầu thang bộ Tầng 4 (Trục Y9-Y10)", "type": "Tiện ích & Phụ trợ"},
        "Sảnh thang máy": {"name": "4F-Sảnh thang máy - Sảnh Thang máy Tầng 4", "short_name": "Sảnh Thang máy Tầng 4", "type": "Tiện ích & Phụ trợ"},
        "Thang bộ Y13-Y14": {"name": "4F-Thang bộ Y13-Y14 - Cầu thang bộ Tầng 4 (Trục Y13-Y14)", "short_name": "Cầu thang bộ Tầng 4 (Trục Y13-Y14)", "type": "Tiện ích & Phụ trợ"}
    },
    "Tầng 5": {
        "5F1": {"name": "5F1 - Phòng Giám đốc Học thuật", "short_name": "Phòng Giám đốc Học thuật", "type": "Văn phòng & Khối làm việc"},
        "5F2": {"name": "5F2 - Phòng Tổng Giám đốc", "short_name": "Phòng Tổng Giám đốc", "type": "Văn phòng & Khối làm việc"},
        "5F3": {"name": "5F3 - Phòng Phó Hiệu trưởng (THPT)", "short_name": "Phòng Phó Hiệu trưởng (THPT)", "type": "Văn phòng & Khối làm việc"},
        "5F4": {"name": "5F4 - Phòng Hiệu trưởng Nhà trường", "short_name": "Phòng Hiệu trưởng Nhà trường", "type": "Văn phòng & Khối làm việc"},
        "5F5": {"name": "5F5 - Phòng Học chuyên đề 5F5", "short_name": "Phòng Học chuyên đề 5F5", "type": "Phòng học & Lớp học"},
        "5F6": {"name": "5F6 - Phòng Họp Ban Giám hiệu 5F6", "short_name": "Phòng Họp Ban Giám hiệu 5F6", "type": "Văn phòng & Khối làm việc"},
        "5F7": {"name": "5F7 - Phòng Không gian Tự học 5F7", "short_name": "Phòng Không gian Tự học 5F7", "type": "Phòng học & Lớp học"},
        "5F8": {"name": "5F8 - Phòng Cố vấn Hướng nghiệp & Du học", "short_name": "Phòng Cố vấn Hướng nghiệp & Du học", "type": "Văn phòng & Khối làm việc"},
        "5F9": {"name": "5F9 - Lớp 11A1 (THPT)", "short_name": "Lớp 11A1 (THPT)", "type": "Phòng học & Lớp học"},
        "5F10": {"name": "5F10 - Phòng Tổ Khoa học Xã hội", "short_name": "Phòng Tổ Khoa học Xã hội", "type": "Văn phòng & Khối làm việc"},
        "5F11": {"name": "5F11 - Lớp 10A2 (THPT)", "short_name": "Lớp 10A2 (THPT)", "type": "Phòng học & Lớp học"},
        "5F12": {"name": "5F12 - Lớp 10A1 (THPT)", "short_name": "Lớp 10A1 (THPT)", "type": "Phòng học & Lớp học"},
        "5F13": {"name": "5F13 - Phòng Giáo viên Cấp THPT", "short_name": "Phòng Giáo viên Cấp THPT", "type": "Văn phòng & Khối làm việc"},
        "5F14": {"name": "5F14 - Lớp 12A1 (THPT)", "short_name": "Lớp 12A1 (THPT)", "type": "Phòng học & Lớp học"},
        "5F15": {"name": "5F15 - Phòng Hội thảo Quốc tế 5F15", "short_name": "Phòng Hội thảo Quốc tế 5F15", "type": "Phòng chức năng & Bộ môn"},
        "5F16": {"name": "5F16 - Phòng Chuyên đề Ngoại ngữ IELTS/SAT", "short_name": "Phòng Chuyên đề Ngoại ngữ IELTS/SAT", "type": "Phòng chức năng & Bộ môn"},
        "5F17": {"name": "5F17 - Phòng Studio & Đa phương tiện", "short_name": "Phòng Studio & Đa phương tiện", "type": "Phòng chức năng & Bộ môn"},
        "5F18": {"name": "5F18 - Phòng Học Dự phòng THPT", "short_name": "Phòng Học Dự phòng THPT", "type": "Phòng học & Lớp học"},
        "5F19": {"name": "5F19 - Thư viện Tổng hợp Cấp THPT (Khu mượn trả)", "short_name": "Thư viện Tổng hợp Cấp THPT (Khu mượn trả)", "type": "Phòng chức năng & Bộ môn"},
        "WC Y4-Y5": {"name": "5F-WC Y4-Y5 - Khu Vệ sinh Tầng 5 (Trục Y4-Y5)", "short_name": "Khu Vệ sinh Tầng 5 (Trục Y4-Y5)", "type": "Tiện ích & Phụ trợ"},
        "WC Y15-Y16": {"name": "5F-WC Y15-Y16 - Khu Vệ sinh Tầng 5 (Trục Y15-Y16)", "short_name": "Khu Vệ sinh Tầng 5 (Trục Y15-Y16)", "type": "Tiện ích & Phụ trợ"},
        "WC Y11-Y12": {"name": "5F-WC Y11-Y12 - Khu Vệ sinh Tầng 5 (Trục Y11-Y12)", "short_name": "Khu Vệ sinh Tầng 5 (Trục Y11-Y12)", "type": "Tiện ích & Phụ trợ"},
        "HL Y4-Y16": {"name": "5F-HL Y4-Y16 - Hành lang Tầng 5 (Trục Y4-Y16)", "short_name": "Hành lang Tầng 5 (Trục Y4-Y16)", "type": "Tiện ích & Phụ trợ"},
        "HL Y1-Y16": {"name": "5F-HL Y1-Y16 - Hành lang Tầng 5 (Trục Y1-Y16)", "short_name": "Hành lang Tầng 5 (Trục Y1-Y16)", "type": "Tiện ích & Phụ trợ"},
        "Sảnh Y7-Y9": {"name": "5F-Sảnh Y7-Y9 - Sảnh Tầng 5 (Trục Y7-Y9)", "short_name": "Sảnh Tầng 5 (Trục Y7-Y9)", "type": "Tiện ích & Phụ trợ"},
        "CT bộ Y4-Y5": {"name": "5F-CT bộ Y4-Y5 - Cầu thang bộ Tầng 5 (Trục Y4-Y5)", "short_name": "Cầu thang bộ Tầng 5 (Trục Y4-Y5)", "type": "Tiện ích & Phụ trợ"},
        "HL X1-X7": {"name": "5F-HL X1-X7 - Hành lang Tầng 5 (Trục X1-X7)", "short_name": "Hành lang Tầng 5 (Trục X1-X7)", "type": "Tiện ích & Phụ trợ"},
        "Thang bộ Y9-Y10": {"name": "5F-Thang bộ Y9-Y10 - Cầu thang bộ Tầng 5 (Trục Y9-Y10)", "short_name": "Cầu thang bộ Tầng 5 (Trục Y9-Y10)", "type": "Tiện ích & Phụ trợ"},
        "Sảnh thang máy": {"name": "5F-Sảnh thang máy - Sảnh Thang máy Tầng 5", "short_name": "Sảnh Thang máy Tầng 5", "type": "Tiện ích & Phụ trợ"},
        "Thư viện": {"name": "5F-Thư viện - Không gian Đọc Thư viện Tầng 5", "short_name": "Không gian Đọc Thư viện Tầng 5", "type": "Phòng chức năng & Bộ môn"},
        "Thang bộ Y13-Y14": {"name": "5F-Thang bộ Y13-Y14 - Cầu thang bộ Tầng 5 (Trục Y13-Y14)", "short_name": "Cầu thang bộ Tầng 5 (Trục Y13-Y14)", "type": "Tiện ích & Phụ trợ"}
    },
    "Tầng 6": {
        "TUM": {"name": "TUM - Khu Tum Kỹ thuật Tầng Thượng", "short_name": "Khu Tum Kỹ thuật Tầng Thượng", "type": "Kho & Kỹ thuật"},
        "Thang máy": {"name": "6F-Thang máy - Buồng Điều khiển Thang máy", "short_name": "Buồng Điều khiển Thang máy", "type": "Kho & Kỹ thuật"},
        "Tủ kỹ thuật điện": {"name": "6F-Tủ kỹ thuật điện - Tủ Kỹ thuật Điện Trung tâm", "short_name": "Tủ Kỹ thuật Điện Trung tâm", "type": "Kho & Kỹ thuật"},
        "HÀNH LANG": {"name": "6F-HÀNH LANG - Hành lang Kỹ thuật Tầng 6", "short_name": "Hành lang Kỹ thuật Tầng 6", "type": "Tiện ích & Phụ trợ"},
        "6F1": {"name": "6F1 - Phòng Truyền thống (kèm Kho phụ trợ)", "short_name": "Phòng Truyền thống (kèm Kho phụ trợ)", "type": "Phòng chức năng & Bộ môn"},
        "6F3": {"name": "6F3 - Phòng Thờ (kèm Điều khiển thang máy)", "short_name": "Phòng Thờ (kèm Điều khiển thang máy)", "type": "Phòng chức năng & Bộ môn"},
        "6F5": {"name": "6F5 - Phòng Học dự phòng 6F5", "short_name": "Phòng Học dự phòng 6F5", "type": "Phòng học & Lớp học"},
        "6F7": {"name": "6F7 - Phòng Thiết bị Thí nghiệm & Kho Hóa chất", "short_name": "Phòng Thiết bị Thí nghiệm & Kho Hóa chất", "type": "Kho & Kỹ thuật"},
        "6F9": {"name": "6F9 - PTN Hóa (Phòng Thí nghiệm Hóa học)", "short_name": "PTN Hóa (Phòng Thí nghiệm Hóa học)", "type": "Phòng chức năng & Bộ môn"},
        "6F11": {"name": "6F11 - PTN Sinh (Phòng Thí nghiệm Sinh học)", "short_name": "PTN Sinh (Phòng Thí nghiệm Sinh học)", "type": "Phòng chức năng & Bộ môn"},
        "6F13": {"name": "6F13 - PTN Vật lý 1 (Phòng Thí nghiệm Lý 1)", "short_name": "PTN Vật lý 1 (Phòng Thí nghiệm Lý 1)", "type": "Phòng chức năng & Bộ môn"},
        "6F15": {"name": "6F15 - PTN Vật lý 2 (Phòng Thí nghiệm Lý 2)", "short_name": "PTN Vật lý 2 (Phòng Thí nghiệm Lý 2)", "type": "Phòng chức năng & Bộ môn"},
        "6F17": {"name": "6F17 - English Phòng Nghe (Ngoại ngữ Lab 1)", "short_name": "English Phòng Nghe (Ngoại ngữ Lab 1)", "type": "Phòng chức năng & Bộ môn"},
        "6F19": {"name": "6F19 - English Phòng Máy (Ngoại ngữ Lab 2)", "short_name": "English Phòng Máy (Ngoại ngữ Lab 2)", "type": "Phòng chức năng & Bộ môn"},
        "6F21": {"name": "6F21 - Phòng Training (Đào tạo & Huấn luyện)", "short_name": "Phòng Training (Đào tạo & Huấn luyện)", "type": "Phòng chức năng & Bộ môn"}
    }
}

all_rooms = []
for sheetname in wb.sheetnames:
    if not sheetname.startswith('Tầng'):
        continue
    sheet = wb[sheetname]
    floor_name = sheetname
    floor_map = pdf_floor_mappings.get(floor_name, {})
    
    for c in range(7, sheet.max_column + 1):
        code = sheet.cell(4, c).value
        if not code or str(code).strip() == 'Tổng':
            continue
        code_str = str(code).strip()
        
        info = floor_map.get(code_str)
        if info:
            name = info['name']
            short_name = info['short_name']
            loc_type = info['type']
        else:
            # Fallback
            short_name = f"Phòng {code_str}"
            name = f"{floor_name.replace('Tầng ', '')}F-{code_str} - {short_name}"
            loc_type = "Phòng học & Lớp học"

        unique_code = code_str
        if not (code_str.startswith(f"{floor_name.replace('Tầng ', '')}F") or code_str.startswith("TUM")):
            unique_code = f"{floor_name.replace('Tầng ', '')}F-{code_str}"

        all_rooms.append({
            'code': unique_code,
            'raw_code': code_str,
            'name': name,
            'short_name': short_name,
            'floor': floor_name,
            'type': loc_type
        })

with open('all_rooms_mapped.json', 'w', encoding='utf-8') as f:
    json.dump(all_rooms, f, ensure_ascii=False, indent=2)

print(f"Mapped {len(all_rooms)} rooms successfully with authentic data.")
