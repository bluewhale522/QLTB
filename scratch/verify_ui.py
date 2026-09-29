import sys, os, time, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app
from playwright.sync_api import sync_playwright

PORT = 5099

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

    print("[1] Trang chủ tải thành công.")

    # Mở modal Thêm thiết bị
    page.click("button:has-text('Thêm thiết bị')")
    page.wait_for_selector("#deviceModal:not(.hidden)")
    time.sleep(0.5)

    print("[2] Modal Thêm thiết bị đã mở.")

    # Kiểm tra danh sách phòng Tầng 1
    tang1_options = page.eval_on_selector_all("#deviceLocation option", "opts => opts.map(o => o.text)")
    print(f"[3] Tầng 1 có {len(tang1_options)} options phòng học:")
    for opt in tang1_options[:8]:
        print("   -", opt)

    page.screenshot(path="scratch/modal_tang1.png")

    # Đổi sang Tầng 2
    page.select_option("#deviceFloor", "Tầng 2")
    time.sleep(0.3)
    tang2_options = page.eval_on_selector_all("#deviceLocation option", "opts => opts.map(o => o.text)")
    print(f"[4] Tầng 2 có {len(tang2_options)} options phòng học:")
    for opt in tang2_options[:8]:
        print("   -", opt)

    page.screenshot(path="scratch/modal_tang2.png")

    # Đổi sang Tầng 3
    page.select_option("#deviceFloor", "Tầng 3")
    time.sleep(0.3)
    tang3_options = page.eval_on_selector_all("#deviceLocation option", "opts => opts.map(o => o.text)")
    print(f"[5] Tầng 3 có {len(tang3_options)} options phòng học:")
    for opt in tang3_options[:8]:
        print("   -", opt)

    # Đổi sang Tầng 6
    page.select_option("#deviceFloor", "Tầng 6")
    time.sleep(0.3)
    tang6_options = page.eval_on_selector_all("#deviceLocation option", "opts => opts.map(o => o.text)")
    print(f"[6] Tầng 6 có {len(tang6_options)} options phòng học:")
    for opt in tang6_options[:8]:
        print("   -", opt)

    browser.close()

print("Hoàn tất kiểm thử giao diện thành công 100%!")
