import shutil
import os
import datetime
from django.shortcuts import render

# 1. Hàm đệ quy tính tổng dung lượng thư mục
def get_folder_size(folder_path):
    total_size = 0
    try:
        for entry in os.scandir(folder_path):
            if entry.is_file(follow_symlinks=False):
                total_size += entry.stat(follow_symlinks=False).st_size
            elif entry.is_dir(follow_symlinks=False):
                total_size += get_folder_size(entry.path)
    except Exception:
        pass # Bỏ qua nếu gặp lỗi quyền truy cập
    return total_size

def dashboard_view(request):
    # 2. Lấy các tham số từ URL (GET)
    selected_drive = request.GET.get('drive', 'C:')
    sort_by = request.GET.get('sort', 'name_asc')
    show_modal = request.GET.get('show_modal', 'false')
    calc_size = request.GET.get('calc_size', 'false')
    search_query = request.GET.get('q', '').strip()
    
    # 3. Thiết lập đường dẫn
    root_path = f"{selected_drive}\\"
    current_path = request.GET.get('path', root_path)

    # Bảo mật: Đảm bảo người dùng không truy cập ngoài ổ đĩa đã chọn
    if not current_path.startswith(selected_drive):
        current_path = root_path

    # 4. Quét dung lượng tổng của ổ đĩa (luôn hiển thị vì nó rất nhanh)
    try:
        usage = shutil.disk_usage(root_path)
        he_so_gb = 1024 ** 3
        tong_dung_luong = round(usage.total / he_so_gb, 1)
        da_su_dung = round(usage.used / he_so_gb, 1)
        phan_tram = round((usage.used / usage.total) * 100)
    except Exception:
        tong_dung_luong, da_su_dung, phan_tram = 0, 0, 0

    file_list = []
    
    # 5. Xử lý danh sách tệp tin
    if os.path.exists(current_path):
        # TRƯỜNG HỢP A: TÌM KIẾM (Quét sâu vào thư mục con)
        if search_query:
            count = 0
            for root, dirs, files in os.walk(current_path):
                for name in dirs + files:
                    if search_query.lower() in name.lower():
                        full_p = os.path.join(root, name)
                        try:
                            stat = os.stat(full_p)
                            is_dir = os.path.isdir(full_p)
                            file_list.append({
                                'name': name,
                                'full_path': full_p,
                                'is_dir': is_dir,
                                'size': round(stat.st_size / (1024*1024), 2) if not is_dir else 0,
                                'is_scanned': not is_dir,
                                'date': datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M'),
                                'timestamp': stat.st_mtime
                            })
                            count += 1
                            if count >= 50: break # Giới hạn để không bị treo máy
                        except: pass
                if count >= 50: break
        
        # TRƯỜNG HỢP B: DUYỆT FILE BÌNH THƯỜNG (Chỉ quét tầng hiện tại)
        else:
            try:
                with os.scandir(current_path) as entries:
                    for entry in entries:
                        try:
                            stat = entry.stat()
                            size_mb = 0
                            is_scanned = False
                            
                            if entry.is_dir():
                                if calc_size == 'true':
                                    size_mb = round(get_folder_size(entry.path) / (1024*1024), 2)
                                    is_scanned = True
                                else:
                                    size_mb = 0
                                    is_scanned = False
                            else:
                                size_mb = round(stat.st_size / (1024*1024), 2)
                                is_scanned = True
                            
                            file_list.append({
                                'name': entry.name,
                                'full_path': entry.path,
                                'is_dir': entry.is_dir(),
                                'size': size_mb,
                                'is_scanned': is_scanned,
                                'date': datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M'),
                                'timestamp': stat.st_mtime
                            })
                        except: pass
            except: pass

    # 6. Thuật toán sắp xếp (Sorting)
    if sort_by == 'name_asc':
        file_list.sort(key=lambda x: x['name'].lower())
    elif sort_by == 'name_desc':
        file_list.sort(key=lambda x: x['name'].lower(), reverse=True)
    elif sort_by == 'size_desc':
        file_list.sort(key=lambda x: x['size'], reverse=True)
    elif sort_by == 'size_asc':
        file_list.sort(key=lambda x: x['size'])
    elif sort_by == 'date_desc':
        file_list.sort(key=lambda x: x['timestamp'], reverse=True)
    elif sort_by == 'date_asc':
        file_list.sort(key=lambda x: x['timestamp'])

    # 7. Tính đường dẫn thư mục cha để quay lại
    parent_path = os.path.dirname(current_path.rstrip('\\'))
    if len(parent_path) < 3: 
        parent_path = root_path

    # 8. Gửi dữ liệu sang HTML
    context = {
        'tong_dung_luong': tong_dung_luong,
        'da_su_dung': da_su_dung,
        'phan_tram': phan_tram,
        'selected_drive': selected_drive,
        'current_path': current_path,
        'parent_path': parent_path,
        'is_root': current_path == root_path,
        'file_list': file_list,
        'sort_by': sort_by,
        'show_modal': show_modal,
        'calc_size': calc_size,
        'search_query': search_query,
    }
    
    return render(request, 'dashboard.html', context)

def teptin_view(request):
    # Logic for handling "Tệp tin" page
    return render(request, 'teptin.html')