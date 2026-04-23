import os
import shutil
import datetime

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm

from .utils import get_file_properties


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


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


def dashboard_view(request):
    selected_drive = request.GET.get('drive', 'C:')
    sort_by = request.GET.get('sort', 'name_asc')
    show_modal = request.GET.get('show_modal', 'false')
    calc_size = request.GET.get('calc_size', 'false')

    root_path = f"{selected_drive}\\"
    current_path = request.GET.get('path', root_path)

    if not current_path.startswith(selected_drive):
        current_path = root_path

    try:
        usage = shutil.disk_usage(root_path)
        he_so = 1024 ** 3
        tong_dung_luong = round(usage.total / he_so, 1)
        da_su_dung = round(usage.used / he_so, 1)
        phan_tram = round((usage.used / usage.total) * 100)
    except Exception:
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
                            if calc_size == 'true':
                                size_bytes = get_folder_size(entry.path)
                                size_mb = round(size_bytes / (1024 * 1024), 2)
                                is_scanned = True
                            else:
                                size_mb = 0
                                is_scanned = False
                        else:
                            size_mb = round(stat.st_size / (1024 * 1024), 2)
                            is_scanned = True

                        file_info = get_file_properties(entry.path)

                        file_list.append({
                            'name': entry.name,
                            'full_path': entry.path,
                            'is_dir': entry.is_dir(),
                            'size': size_mb,
                            'is_scanned': is_scanned,
                            'date': datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M'),
                            'timestamp': stat.st_mtime,
                            'properties': file_info,
                        })
                    except Exception:
                        pass
        except Exception:
            pass

    if sort_by == 'name_asc':
        file_list.sort(key=lambda x: x['name'].lower())
    elif sort_by == 'name_desc':
        file_list.sort(key=lambda x: x['name'].lower(), reverse=True)
    elif sort_by == 'size_asc':
        file_list.sort(key=lambda x: x['size'])
    elif sort_by == 'size_desc':
        file_list.sort(key=lambda x: x['size'], reverse=True)
    elif sort_by == 'date_asc':
        file_list.sort(key=lambda x: x['timestamp'])
    elif sort_by == 'date_desc':
        file_list.sort(key=lambda x: x['timestamp'], reverse=True)

    parent_path = root_path
    is_root = current_path.rstrip("\\") == root_path.rstrip("\\")
    if not is_root:
        parent_path = os.path.dirname(current_path.rstrip("\\")) + "\\"

    context = {
        'tong_dung_luong': tong_dung_luong,
        'da_su_dung': da_su_dung,
        'phan_tram': phan_tram,
        'selected_drive': selected_drive,
        'current_path': current_path,
        'file_list': file_list,
        'sort_by': sort_by,
        'show_modal': show_modal,
        'calc_size': calc_size,
        'parent_path': parent_path,
        'is_root': is_root,
    }
    return render(request, 'dashboard.html', context)