import subprocess
import os
import sys

# Lấy chính xác thư mục đang chứa file FileBox.exe
base_dir = os.path.dirname(os.path.abspath(sys.executable))

# Ép đường dẫn tuyệt đối tới Python và file run_desktop
python_exe = os.path.join(base_dir, 'venv', 'Scripts', 'python.exe')
run_script = os.path.join(base_dir, 'run_desktop.py')

print(f"Đang khởi động từ: {base_dir}")
print(f"Đường dẫn Python: {python_exe}")

# Khởi chạy
subprocess.call([python_exe, run_script])