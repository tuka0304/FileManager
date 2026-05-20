import multiprocessing
import threading
import webview
import sys
import os
import time
import traceback

def start_django_server():
    try:
        # 1. BẮT BUỘC: Khai báo định vị file settings cho Django
        # (Giả định thư mục gốc dự án của sếp tên là FileManager)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FileManager.settings')
        
        # 2. Ép thư mục làm việc về đúng chỗ chứa file .exe
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(base_dir)

        # 3. Gọi lõi Django
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8000', '--noreload'])
        
    except Exception as e:
        # TUYỆT CHIÊU: Nếu Server sập, bắt nó ghi lỗi ra file text để bắt mạch!
        with open("crash_log.txt", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())

if __name__ == '__main__':
    multiprocessing.freeze_support() 
    
    # Khởi động Server
    server_thread = threading.Thread(target=start_django_server)
    server_thread.daemon = True
    server_thread.start()

    # Chờ 3 giây cho Server khởi động xong
    time.sleep(3) 

    # Bung giao diện
    webview.create_window('FileBox', 'http://127.0.0.1:8000/')
    webview.start(gui='edgechromium')