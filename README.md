# HỆ THỐNG QUẢN LÝ THIẾT BỊ TRƯỜNG HỌC (QLTB)

Hệ thống Web App toàn diện phục vụ quản lý thiết bị, tài sản, phòng bộ môn, theo dõi mượn - trả và lịch sử luân chuyển thiết bị trong trường học.

---

## 🌟 TÍNH NĂNG CHÍNH

### 1. 📋 Quản lý Thiết bị (Equipment Management)
- **Thêm thiết bị thủ công**: Nhập đầy đủ thông tin: Mã thiết bị, Tên thiết bị, Danh mục, Vị trí hiện tại/Phòng học đang sử dụng, Trạng thái, Nguyên giá, Ngày nhập, Nhà cung cấp, Cấu hình thông số kỹ thuật, Ghi chú.
- **Kiểm soát mã thiết bị duy nhất (Unique Asset ID)**: Chống trùng lặp mã thiết bị cả ở giao diện lẫn cơ sở dữ liệu.
- **Nhập thiết bị hàng loạt bằng File CSV**:
  - Hỗ trợ tải tệp CSV mẫu chuẩn (`mau_nhap_thiet_bi.csv`).
  - Tự động kiểm tra trùng lặp mã thiết bị trong database và phát hiện trùng lặp ngay trong tệp CSV.
  - Báo cáo số lượng nhập thành công và danh sách các dòng bị lỗi chi tiết.
- **Phân loại đa dạng**: Máy tính & Thiết bị số, Máy chiếu & Trình chiếu, Dụng cụ Thí nghiệm Khoa học, Dụng cụ Thể thao, Thiết bị Âm thanh & Sự kiện, Thiết bị Văn phòng,...
- **Theo dõi trạng thái**: `Sẵn sàng` (Trong kho), `Đang sử dụng`, `Đang mượn`, `Hỏng`, `Bảo trì`, `Đã thanh lý`.
- **Bộ lọc & Tìm kiếm tức thì**: Lọc theo từ khóa, danh mục, phòng học/vị trí, trạng thái.

---

### 2. 🚚 Theo dõi Vị trí & Lịch sử Di chuyển (Movement Tracking)
- **Quản lý vị trí đang sử dụng**: Biết chính xác từng thiết bị đang được lắp đặt/sử dụng ở phòng nào (Phòng Tin học 1, Phòng Thí nghiệm Hóa, Kho Trung tâm, Hội trường A,...).
- **Chức năng Điều chuyển thiết bị**:
  - Hiển thị rõ: **Vị trí trước khi chuyển** $\rightarrow$ **Vị trí sau khi chuyển**.
  - Ghi nhận ngày giờ di chuyển, người thực hiện (Mã NV/GV/Cán bộ), lý do di chuyển.
  - Tự động lưu vào lịch sử di chuyển phục vụ công tác thanh tra, kiểm kê tài sản.
  - Xem tab "Lịch sử di chuyển" tổng thể hoặc xem ngay trong modal chi tiết của từng thiết bị.

---

### 3. 🔄 Quản lý Mượn - Trả Thiết bị (Borrow & Return)
- **Tạo yêu cầu mượn thiết bị**:
  - Dựa trên **Mã Giáo viên** (`GV001`, `GV002`...) và **Mã Thiết bị** (`TB-PC-001`, `TB-MC-002`...).
  - Gắn liền với Phòng ban / Tổ bộ môn của giáo viên.
  - Ngày mượn, hạn trả dự kiến, mục đích sử dụng.
  - Kiểm tra trạng thái thiết bị: Chỉ cho phép mượn thiết bị đang "Sẵn sàng".
- **Duyệt mượn**: Trạng thái `Chờ duyệt` $\rightarrow$ `Đang mượn` $\rightarrow$ `Đã trả` (hoặc `Từ chối`).
- **Ghi nhận thu hồi / Trả thiết bị**:
  - Đánh giá tình trạng khi hoàn trả: `Tốt`, `Bình thường`, `Hư hỏng nhẹ`, `Hỏng nặng`, `Mất phụ kiện`.
  - Nếu trả về với tình trạng hư hỏng, hệ thống tự động đổi trạng thái thiết bị sang `Hỏng` để đưa vào danh sách bảo trì.
- **Cảnh báo Quá hạn (Overdue Alert)**:
  - Tự động tính toán số ngày quá hạn theo thời gian thực.
  - Hiển thị cảnh báo trực quan trên Dashboard và bảng mượn trả bằng badge màu đỏ.

---

### 4. 👤 Quản lý Người dùng & Phòng ban (Users & Departments)
- Quản lý danh sách Cán bộ, Giáo viên, Nhân viên theo Mã GV, Họ tên, Email, SĐT, Tổ bộ môn/Phòng ban.
- Quản lý danh mục Phòng học, Phòng thí nghiệm, Hội trường, Kho bãi.
- Chức năng chuyển đổi nhanh vai trò người dùng (Admin, GV Vật lý, GV Tin học, Kỹ thuật viên) ngay trên thanh tiêu đề để trải nghiệm hệ thống từ nhiều góc nhìn.

---

### 5. 📊 Báo cáo & Thống kê (Reports & Export)
- Dashboard biểu đồ trực quan (Doughnut Chart phân loại thiết bị, Bar Chart số lượng thiết bị theo phòng ban).
- Bảng xếp hạng Top thiết bị được mượn nhiều nhất, Top giáo viên/phòng ban mượn nhiều nhất.
- Danh sách thiết bị hỏng cần thanh lý hoặc sửa chữa.
- **Xuất dữ liệu Excel (.xlsx)**:
  - Xuất danh mục toàn bộ thiết bị.
  - Xuất sổ theo dõi mượn - trả thiết bị.
  - Xuất nhật ký lịch sử di chuyển thiết bị.

---

### 6. ⚙️ Hệ thống & Bảo mật (System & Administration)
- Sao lưu (Backup) toàn bộ dữ liệu ra tệp JSON.
- Phục hồi (Restore) dữ liệu từ tệp JSON.
- Nạp lại dữ liệu mẫu (Reset demo data) với các thiết bị học đường thực tế.
- Nhật ký hoạt động hệ thống (Audit Trail) ghi lại mọi thao tác thêm, xóa, sửa, di chuyển, mượn trả.

---

## 🚀 HƯỚNG DẪN KHỞI CHẠY

### Cách 1: Chạy bằng file `run.bat` (Khuyên dùng trên Windows)
Chỉ cần nhấp đúp vào file `run.bat` trong thư mục dự án. Hệ thống sẽ tự động khởi động máy chủ Flask và mở trình duyệt web tại địa chỉ `http://127.0.0.1:5000`.

### Cách 2: Chạy bằng dòng lệnh
Mở PowerShell hoặc Command Prompt tại thư mục dự án và gõ:
```bash
python app.py
```
Sau đó mở trình duyệt và truy cập `http://127.0.0.1:5000`.

---

## 📂 CẤU TRÚC DỰ ÁN

```
QLTB/
├── app.py                # Máy chủ Flask & RESTful API
├── database.py           # Quản lý kết nối SQLite và khởi tạo bảng
├── seed_data.py          # Dữ liệu mẫu học đường phong phú ban đầu
├── sample_import.csv     # Tệp CSV mẫu để thử nghiệm nhập thiết bị hàng loạt
├── run.bat               # File chạy một chạm trên Windows
├── templates/
│   └── index.html        # Giao diện chính Single Page App (Tailwind CSS + Lucide Icons)
├── static/
│   ├── css/
│   │   └── custom.css    # Hiệu ứng, kiểu dáng huy hiệu và hoạt ảnh
│   └── js/
│       └── app.js        # Logic xử lý giao diện, gọi API, biểu đồ, xuất file Excel
└── README.md             # Tài liệu hướng dẫn sử dụng chi tiết
```
