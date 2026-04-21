import shutil
import os
import datetime
from django.shortcuts import render

def get_folder_size(folder_path):
    total_size = 0
    try:
        for entry in os.scandir(folder_path):
            if entry.is_file(follow_symlinks=False):
                total_size += entry.stat(follow_symlinks=False).st_size
            elif entry.is_dir(follow_symlinks=False):
                total_size += get_folder_size(entry.path)
    except Exception:
        pass
    return total_size

def dashboard_view(request):
    selected_drive = request.GET.get('drive', 'C:')
    sort_by = request.GET.get('sort', 'name_asc')
    show_modal = request.GET.get('show_modal', 'false')
    
    # 1. Thêm tham số xác nhận việc quét dung lượng (mặc định là false)
    calc_size = request.GET.get('calc_size', 'false')
    
    root_path = f"{selected_drive}\\"
    current_path = request.GET.get('path', root_path)

    if not current_path.startswith(selected_drive):
        current_path = root_path

    # Quét dung lượng tổng ổ đĩa (luôn hiển thị vì nó nhanh)
    try:
        usage = shutil.disk_usage(root_path)
        he_so = 1024 ** 3
        tong_dung_luong = round(usage.total / he_so, 1)
        da_su_dung = round(usage.used / he_so, 1)
        phan_tram = round((usage.used / usage.total) * 100)
    except:
        tong_dung_luong, da_su_dung, phan_tram = 0, 0, 0

    file_list = []
    if os.path.exists(current_path):
        try:
            with os.scandir(current_path) as entries:
                for entry in entries:
                    try:
                        stat = entry.stat()
                        size_mb = 0
                        is_scanned = False
                        
                        if entry.is_dir():
                            # 2. Chỉ quét nếu người dùng đã nhấn nút "Load" (calc_size == 'true')
                            if calc_size == 'true':
                                size_bytes = get_folder_size(entry.path)
                                size_mb = round(size_bytes / (1024 * 1024), 2)
                                is_scanned = True
                            else:
                                size_mb = 0
                                is_scanned = False
                        else:
                            # File lẻ thì lấy dung lượng luôn vì nó rất nhanh
                            size_mb = round(stat.st_size / (1024 * 1024), 2)
                            is_scanned = True
                            
                        file_list.append({
                            'name': entry.name,
                            'full_path': entry.path,
                            'is_dir': entry.is_dir(),
                            'size': size_mb,
                            'is_scanned': is_scanned, # Biến này để hiển thị trên HTML
                            'date': datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M'),
                            'timestamp': stat.st_mtime
                        })
                    except: pass
        except: pass

    # Logic sắp xếp giữ nguyên...
    # ...

    context = {
        'tong_dung_luong': tong_dung_luong,
        'da_su_dung': da_su_dung,
        'phan_tram': phan_tram,
        'selected_drive': selected_drive,
        'current_path': current_path,
        'file_list': file_list,
        'sort_by': sort_by,
        'show_modal': show_modal,
        'calc_size': calc_size, # Gửi trạng thái về lại HTML
    }
    return render(request, 'dashboard.html', context)