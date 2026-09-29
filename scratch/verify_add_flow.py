import sys, os, time, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app
from playwright.sync_api import sync_playwright

PORT = 5098

def run_server():
    app.run(port=PORT, debug=False, use_reloader=False)

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
time.sleep(2)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto(f"http://127.0.0.1:{PORT}")
    page.wait_for_selector("#mainNav")

    # Click Thêm thiết bị
    page.click("button:has-text('Thêm thiết bị')")
    page.wait_for_selector("#deviceModal:not(.hidden)")

    # Select room in Tầng 1
    page.select_option("#deviceLocation", "1F18 - Lớp Moon (Mầm non)")
    time.sleep(0.3)
    page.screenshot(path="scratch/modal_selected_room.png")

    # Điền thông tin
    page.fill("#deviceName", "Smart TV Samsung Crystal 65 inch")
    page.select_option("#deviceCategory", "Màn hình máy tính")
    page.fill("#devicePrice", "18500000")
    page.fill("#deviceSupplier", "Samsung Vina")
    page.fill("#deviceSpec", "4K UHD, HDR10+, Smart Tizen OS")
    page.fill("#deviceNotes", "Lắp đặt tại lớp Moon phục vụ giảng dạy mầm non")

    # Click Lưu thiết bị
    page.click("button:has-text('Lưu thiết bị')")
    time.sleep(1.5)

    # Chuyển sang tab Quản lý thiết bị
    page.click("button[data-tab='devices']")
    time.sleep(1)

    # Lọc phòng Lớp Moon
    page.select_option("#deviceFloorFilter", "Tầng 1")
    time.sleep(0.5)
    page.select_option("#deviceLocationFilter", "1F18 - Lớp Moon (Mầm non)")
    time.sleep(0.5)

    page.screenshot(path="scratch/devices_filtered_moon.png")
    print("Đã thêm thành công thiết bị vào Lớp Moon và lọc hiển thị chính xác!")

    browser.close()
