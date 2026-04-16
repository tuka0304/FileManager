import shutil
import os # Thêm thư viện os để kiểm tra ổ đĩa
from django.shortcuts import render

def dashboard_view(request):
    # 1. Lắng nghe xem người dùng đang chọn ổ đĩa nào từ giao diện (Mặc định là ổ C:)
    selected_drive = request.GET.get('drive', 'C:')
    
    # 2. Kiểm tra an toàn: Nếu máy tính không có ổ D hay E mà người dùng vẫn cố chọn, thì tự quay về ổ C
    drive_path = f"{selected_drive}\\" # Thêm dấu \ để thành đường dẫn chuẩn, VD: C:\
    if not os.path.exists(drive_path):
        selected_drive = 'C:'
        drive_path = 'C:\\'

    # 3. Quét đúng ổ đĩa đã chọn
    thong_so_o_dia = shutil.disk_usage(drive_path) 
    
    # 4. Tính toán số liệu
    he_so = 1024 ** 3
    tong_dung_luong = round(thong_so_o_dia.total / he_so, 1)
    da_su_dung = round(thong_so_o_dia.used / he_so, 1)
    phan_tram_su_dung = round((thong_so_o_dia.used / thong_so_o_dia.total) * 100)

    # 5. Gói hàng gửi về HTML (Gửi kèm cả tên ổ đĩa đang chọn để HTML hiển thị đúng)
    context = {
        'tong_dung_luong': tong_dung_luong,
        'da_su_dung': da_su_dung,
        'phan_tram': phan_tram_su_dung,
        'selected_drive': selected_drive, # Biến này giúp thẻ <select> giữ nguyên giá trị vừa chọn
    }

    return render(request, 'dashboard.html', context)