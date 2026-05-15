import webview
import subprocess
import time
import sys
import os
import ctypes
# --- MA THUẬT ÉP ĐỔI ICON TASKBAR BẰNG WINDOWS API ---
try:
    # Tạo một mã định danh độc quyền cho phần mềm của CEO Hoàng Phi
    myappid = 'hoangphi.filebox.desktop.1.0' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass
# ------------------------------------------------------
def start_django_server():
    print("🚀 Đang khởi động lõi hệ thống FileBox...")
    # Chạy server Django ngầm
    process = subprocess.Popen(
        [sys.executable, 'manage.py', 'runserver', '127.0.0.1:8000', '--noreload'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return process

if __name__ == '__main__':
    # 1. Bật server ngầm
    server_process = start_django_server()
    
    # 2. Đợi 2 giây cho server khởi động
    time.sleep(2)
    
    # 3. ĐƯỜNG DẪN TỚI FILE ICON CỦA BẠN (Dùng đường dẫn tuyệt đối cho chắc chắn)
    # Giả sử bạn để file 'app_icon.ico' cùng thư mục với file 'run_desktop.py' này
    
    
    # 4. Tạo và mở cửa sổ phần mềm Desktop xịn sò, thêm tham số icon
    print("💻 Đang mở giao diện Desktop...")
    webview.create_window(
        title='FileBox - Tổng bộ Quản trị Hệ thống', 
        url='http://127.0.0.1:8000',
        width=1280, 
        height=800,
        min_size=(1024, 768)
    )
    
    # ĐƯỜNG DẪN TỚI FILE ICON CỦA BẠN
    icon_path = os.path.join(os.path.dirname(__file__), 'logo.ico')
    
    # 4. CHUYỂN ICON XUỐNG ĐÂY
    webview.start(icon=icon_path)
    
    # 5. Khi bạn nhấn dấu X tắt phần mềm
    print("🛑 Đang đóng hệ thống và dọn dẹp...")
    server_process.kill()
    sys.exit()