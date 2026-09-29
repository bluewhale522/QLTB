@echo off
chcp 65001 > nul
echo ================================================================
echo    HỆ THỐNG QUẢN LÝ THIẾT BỊ TRƯỜNG HỌC (QLTB)
echo ================================================================
echo.
echo [*] Đang khởi động ứng dụng Web...
echo [*] Mở trình duyệt web tại địa chỉ: http://127.0.0.1:5000
echo.

start "" http://127.0.0.1:5000
python app.py
pause
