import os
import shutil
import datetime
from datetime import timedelta
from collections import defaultdict
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.files.storage import FileSystemStorage
from django.http import FileResponse, JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
import json
import random
from django.core.mail import send_mail
from django.conf import settings
from .forms import FormDangKyTuyChinh

# Import các models của bạn (Đảm bảo trong models.py đã có những class này)
from .models import UserProfile, TransferHistory, SecuredVault, QuickShare, ReceiveHistory, Notification, SecurityLog

from .drive_utils import upload_to_drive, list_drive_files, download_from_drive

# ==========================================
# HÀM BỔ TRỢ
# ==========================================
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

def find_empty_folders(root_path):
    empty_folders = []
    # Danh sách các thư mục "vùng cấm" không được quét
    skip_dirs = {'Windows', 'Program Files', 'Program Files (x86)', '$Recycle.Bin', 'ProgramData', 'System Volume Information'}
    
    try:
        # Dùng topdown=True để có thể can thiệp bỏ qua thư mục con ngay từ trên xuống
        for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
            # Loại bỏ các thư mục hệ thống khỏi danh sách cần duyệt (dirnames)
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]
            
            # Kiểm tra xem thư mục hiện tại có trống không
            # Thư mục trống là thư mục không có file VÀ không có thư mục con nào
            if not dirnames and not filenames:
                empty_folders.append(dirpath)
    except Exception: 
        pass
        
    return empty_folders

def find_duplicate_files(root_path):
    files_info = defaultdict(list)
    duplicates = []
    folder_scanned = 0
    try:
        for dirpath, _, filenames in os.walk(root_path):
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                try:
                    size = os.path.getsize(full_path)
                    if size > 0: files_info[(filename, size)].append(full_path)
                except Exception: pass
            folder_scanned += 1
            if folder_scanned > 2000: break 
    except Exception: pass
    for (name, size), paths in files_info.items():
        if len(paths) > 1:
            duplicates.append({'name': name, 'size': round(size / (1024*1024), 2), 'paths': paths})
    return duplicates

# ==========================================
# 1. AUTHENTICATION (Xác thực người dùng)
# ==========================================
def register_view(request):
    """Xử lý trang dangky.html"""
    if request.method == 'POST':
        form = FormDangKyTuyChinh(request.POST or None)
        if form.is_valid():
            user = form.save()
            # Tạo profile mặc định cho người dùng mới
            UserProfile.objects.create(user=user)
            login(request, user)
            return redirect('trang-chu')
    else:
        form = FormDangKyTuyChinh()
    return render(request, 'dangky.html', {'form': form})

def quen_mat_khau(request):
    step = request.session.get('reset_step', 'email')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'send_otp':
            email = request.POST.get('email')
            user = User.objects.filter(email=email).first()
            if user:
                otp = str(random.randint(100000, 999999))
                request.session['reset_email'] = email
                request.session['reset_otp'] = otp
                request.session['reset_step'] = 'otp'
                
                send_mail(
                    'Mã xác thực khôi phục mật khẩu FileBox',
                    f'Chào bạn, mã OTP 6 số để đổi mật khẩu của bạn là: {otp}',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )
                messages.success(request, 'Mã OTP đã được gửi!')
            else:
                messages.error(request, 'Email chưa được đăng ký.')
            # SỬA LẠI Ở ĐÂY
            return redirect('quen_mat_khau')
            
        elif action == 'verify_otp':
            if request.POST.get('otp') == request.session.get('reset_otp'):
                request.session['reset_step'] = 'new_password'
            else:
                messages.error(request, 'Mã OTP không chính xác.')
            # SỬA LẠI Ở ĐÂY
            return redirect('quen_mat_khau')
            
        elif action == 'change_password':
            user = User.objects.filter(email=request.session.get('reset_email')).first()
            if user:
                user.set_password(request.POST.get('new_password'))
                user.save()
                messages.success(request, 'Đổi mật khẩu thành công!')
                for key in ['reset_step', 'reset_otp', 'reset_email']:
                    if key in request.session: del request.session[key]
                return redirect('login')

    return render(request, 'quenmk.html', {'step': step})

# ==========================================
# 2. CÁC TRANG CHÍNH CỦA HỆ THỐNG FILEBOX
# ==========================================

@login_required
def dashboard_view(request):
    """Xử lý trang dashboard.html (Tổng quan)"""
    selected_drive = request.GET.get('drive', 'C:')
    root_path = f"{selected_drive}\\"
    
    # 1. Quét dung lượng ổ đĩa thật
    try:
        usage = shutil.disk_usage(root_path)
        he_so_gb = 1024 ** 3
        tong_dung_luong = round(usage.total / he_so_gb, 1)
        da_su_dung = round(usage.used / he_so_gb, 1)
        phan_tram = round((usage.used / usage.total) * 100)
    except Exception:
        tong_dung_luong, da_su_dung, phan_tram = 0, 0, 0

    # 2. Gọi hàm lấy 4 file mới nhất
    recent_files = get_recent_files(root_path, limit=4)

    # 3. Lấy 5 hoạt động bảo mật gần nhất
    recent_activities = SecurityLog.objects.filter(user=request.user).order_by('-created_at')[:5]

    # Đẩy toàn bộ dữ liệu thật ra màn hình
    context = {
        'tong_dung_luong': tong_dung_luong,
        'da_su_dung': da_su_dung,
        'phan_tram': phan_tram,
        'selected_drive': selected_drive,
        'recent_files': recent_files,
        'recent_activities': recent_activities,
    }
    return render(request, 'dashboard.html', context)

@login_required
def teptin_view(request):
    """Xử lý trang teptin.html (Quản lý file chi tiết, Tìm kiếm, Sắp xếp)"""
    # Nếu đang chạy trên máy chủ Render (Web), chuyển hướng tải file Desktop
    if os.environ.get('RENDER') == 'true':
        messages.info(request, 'Tính năng quản lý ổ đĩa sâu chỉ hỗ trợ trên bản Desktop. Đang chuyển hướng đến tab mới để tải về...')
        # URL chính xác tới trang releases của sếp
        return redirect('https://github.com/tuka0304/FileManager/releases')

    selected_drive = request.GET.get('drive', 'C:')
    sort_by = request.GET.get('sort', 'name_asc')
    calc_size = request.GET.get('calc_size', 'false')
    search_query = request.GET.get('q', '').strip()
    
    root_path = f"{selected_drive}\\"
    current_path = request.GET.get('path', root_path)

    if not current_path.startswith(selected_drive):
        current_path = root_path

    file_list = []
    
    if os.path.exists(current_path):
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
                            if count >= 50: break 
                        except: pass
                if count >= 50: break
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

    # Sắp xếp
    if sort_by == 'name_asc': file_list.sort(key=lambda x: x['name'].lower())
    elif sort_by == 'name_desc': file_list.sort(key=lambda x: x['name'].lower(), reverse=True)
    elif sort_by == 'size_desc': file_list.sort(key=lambda x: x['size'], reverse=True)
    elif sort_by == 'size_asc': file_list.sort(key=lambda x: x['size'])
    elif sort_by == 'date_desc': file_list.sort(key=lambda x: x['timestamp'], reverse=True)
    elif sort_by == 'date_asc': file_list.sort(key=lambda x: x['timestamp'])

    parent_path = os.path.dirname(current_path.rstrip('\\'))
    if len(parent_path) < 3: parent_path = root_path

    context = {
        'selected_drive': selected_drive,
        'current_path': current_path,
        'parent_path': parent_path,
        'is_root': current_path == root_path,
        'file_list': file_list,
        'sort_by': sort_by,
        'calc_size': calc_size,
        'search_query': search_query,
    }
    return render(request, 'teptin.html', context)

@login_required
def quetdon_view(request):
    """Xử lý trang quetdon.html"""
    # Nếu đang chạy trên máy chủ Render (Web), chuyển hướng tải file .exe
    if os.environ.get('RENDER') == 'true':
        messages.info(request, 'Tính năng dọn dẹp rác chỉ hỗ trợ trên bản Desktop. Đang chuyển hướng đến trang tải xuống...')
        return redirect('https://github.com/tuka0304/FileManager/releases')

    action = request.GET.get('action', '')
    selected_drive = request.GET.get('drive', 'C:')
    root_path = f"{selected_drive}\\"
    
    empty_folders = []
    duplicates = []
    
    if action == 'empty_folders':
        empty_folders = find_empty_folders(root_path)
    elif action == 'duplicates':
        duplicates = find_duplicate_files(root_path)
        
    return render(request, 'quetdon.html', {
        'action': action,
        'selected_drive': selected_drive,
        'empty_folders': empty_folders,
        'duplicates': duplicates,
    })

@login_required
def delete_scanned_item(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Lấy và chuẩn hóa đường dẫn để tránh lỗi gạch chéo
            item_path = os.path.normpath(data.get('path', ''))
            is_folder = data.get('isFolder') == 'true' or data.get('isFolder') is True

            if not os.path.exists(item_path):
                return JsonResponse({'success': False, 'error': f'Không tìm thấy đường dẫn: {item_path}'})

            # Thực hiện xóa
            if is_folder:
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
            
            return JsonResponse({'success': True})
            
        except PermissionError:
            return JsonResponse({'success': False, 'error': 'Windows từ chối quyền (Permission Denied). Bạn không thể xóa tệp/thư mục hệ thống này!'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Yêu cầu không hợp lệ.'})

@login_required
def chuyenfile_view(request):
    """Xử lý trang chuyenfile.html"""
    context = {}
    error = None
    preview_file = None
    if request.method == 'POST':
        # Gửi tệp
        if 'file_to_share' in request.FILES:
            uploaded_file = request.FILES['file_to_share']
            size_mb = round(uploaded_file.size / (1024 * 1024), 2)
            expiry_minutes = int(request.POST.get('expiry_time', 60))

            share = QuickShare.objects.create(
                sender=request.user,
                file=uploaded_file,
                file_name=uploaded_file.name,
                file_size=size_mb,
                expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
            )
            request.session['recent_pin'] = share.pin_code
            request.session['recent_file'] = share.file_name
            return redirect('chuyen-file')
            
        # Nhận tệp
        elif 'pin_code' in request.POST:
            pin = request.POST.get('pin_code').strip()
            confirm_download = request.POST.get('confirm_download')
            try:
                quick_share = QuickShare.objects.get(pin_code=pin)
                
                if quick_share.expires_at and quick_share.expires_at < timezone.now():
                    error = "Mã PIN này đã hết hạn sử dụng."
                    quick_share.delete()
                else:
                    # Bước 2: Người dùng xác nhận tải
                    if confirm_download:
                        # Tạo bản ghi Lịch sử nhận
                        ReceiveHistory.objects.create(
                            receiver=request.user,
                            file_name=quick_share.file_name,
                            file_size=quick_share.file_size,
                            pin_code=pin,
                        )
                        # Tạo thông báo cho người gửi
                        Notification.objects.create(
                            user=quick_share.sender,
                            message=f"Tệp {quick_share.file_name} vừa được tải xuống bằng mã PIN {pin}."
                        )
                        return FileResponse(quick_share.file.open('rb'), as_attachment=True, filename=quick_share.file_name)
                    
                    # Bước 1: Xem trước thông tin file
                    else:
                        preview_file = quick_share

            except QuickShare.DoesNotExist:
                error = "Mã PIN không hợp lệ hoặc tệp không tồn tại."
            except Exception:
                error = "Đã xảy ra lỗi khi tải tệp. Có thể tệp đã bị xóa."

    sent_qs = QuickShare.objects.filter(sender=request.user).order_by('-created_at')[:10]
    received_qs = ReceiveHistory.objects.filter(receiver=request.user).order_by('-created_at')[:10]
    
    all_history = []
    for item in sent_qs:
        item.action_type = 'sent'
        all_history.append(item)
    for item in received_qs:
        item.action_type = 'received'
        all_history.append(item)
        
    all_history.sort(key=lambda x: x.created_at, reverse=True)
    
    context['all_history'] = all_history[:5]
    context['recent_pin'] = request.session.pop('recent_pin', None)
    context['recent_file'] = request.session.pop('recent_file', None)
    context['error'] = error
    context['preview_file'] = preview_file
    return render(request, 'chuyenfile.html', context)

@login_required
def baomat_view(request):
    """Xử lý trang baomat.html"""
    security_logs = SecurityLog.objects.filter(user=request.user)[:5]
    security_score = 100
    network_security_enabled = request.session.get('network_security', True)
    context = {
        'security_logs': security_logs,
        'security_score': security_score,
        'network_security_enabled': network_security_enabled,
    }
    return render(request, 'baomat.html', context)

@login_required
def scan_security(request):
    SecurityLog.objects.create(
        user=request.user, action="Hoàn tất quét hệ thống", details="Hệ thống an toàn. Không phát hiện phần mềm độc hại hay rò rỉ dữ liệu.", log_type="success"
    )
    return JsonResponse({'success': True, 'message': 'Quét hoàn tất!'})

@login_required
def toggle_network_security(request):
    current_state = request.session.get('network_security', True)
    new_state = not current_state
    request.session['network_security'] = new_state
    
    action_text = "Đã bật tính năng bảo mật mạng" if new_state else "Đã tắt tính năng bảo mật mạng"
    log_type_val = "info" if new_state else "warning"
    
    SecurityLog.objects.create(
        user=request.user, 
        action=action_text, 
        details="Chế độ chặn tracker và bot độc hại", 
        log_type=log_type_val
    )
    
    return JsonResponse({'success': True, 'state': new_state})

@login_required
def kygui_view(request):
    """Xử lý trang kygui.html - Đẩy file lên Google Drive"""
    error = None
    is_locked = not request.session.get('vault_unlocked', False)

    if request.method == 'POST' and request.FILES.get('vault_file'):
        try:
            uploaded_file = request.FILES['vault_file']
            
            # Lưu file xuống ổ cứng (Localhost) thay vì đẩy lên Google Drive
            save_dir = os.path.join('media', 'vault_storage')
            os.makedirs(save_dir, exist_ok=True) # Tự động tạo thư mục media/vault_storage nếu chưa có
            
            fs = FileSystemStorage(location=save_dir)
            saved_filename = fs.save(uploaded_file.name, uploaded_file)
            
            print(f"[DEBUG - SUCCESS] Đã lưu file ký gửi thành công tại: {fs.path(saved_filename)}")
            return redirect('ky-gui')
        except Exception as e:
            error = f"Lỗi lưu file xuống ổ cứng: {str(e)}"
            print(f"[DEBUG - ERROR] Quá trình ký gửi file thất bại: {str(e)}")

    drive_files = []
    if not is_locked:
        try:
            raw_files = list_drive_files(request.user.id)
            for f in raw_files:
                size_bytes = int(f.get('size', 0))
                if size_bytes >= 1024 * 1024:
                    size_str = f"{round(size_bytes / (1024 * 1024), 2)} MB"
                else:
                    size_str = f"{round(size_bytes / 1024, 2)} KB"
                    
                try:
                    dt = datetime.datetime.strptime(f.get('createdTime'), "%Y-%m-%dT%H:%M:%S.%fZ")
                    time_str = dt.strftime("%H:%M - %d/%m/%Y")
                except Exception:
                    time_str = f.get('createdTime')
                    
                drive_files.append({
                    'id': f.get('id'),
                    'name': f.get('name'),
                    'size': size_str,
                    'createdTime': time_str,
                    'mimeType': f.get('mimeType')
                })
        except Exception as e:
            error = f"Lỗi lấy danh sách từ Google Drive: {str(e)}"

    return render(request, 'kygui.html', {'drive_files': drive_files, 'error': error, 'is_locked': is_locked})

@login_required
def unlock_vault(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        if request.user.check_password(password):
            request.session['vault_unlocked'] = True
    return redirect('ky-gui')

@login_required
def lock_vault(request):
    request.session['vault_unlocked'] = False
    return redirect('ky-gui')

@login_required
def download_vault_file(request, file_id):
    if not request.session.get('vault_unlocked', False):
        return redirect('ky-gui')
    
    file_bytes, mime_type, file_name = download_from_drive(file_id)
    response = HttpResponse(file_bytes, content_type=mime_type)
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    return response

@login_required
def caidat_view(request):
    """Xử lý trang caidat.html"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    active_tab = request.GET.get('tab', 'tai-khoan')
    
    if request.method == 'POST':
        tab_action = request.POST.get('tab', active_tab)
        if tab_action == 'tai-khoan':
            email = request.POST.get('email')
            if email is not None:
                request.user.email = email
                request.user.save()
            if 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']
                profile.save()
        elif tab_action == 'cai-dat-chung':
            profile.auto_deep_scan = request.POST.get('auto_deep_scan') == 'on'
            profile.save()
        elif tab_action == 'giao-dien':
            profile.dark_mode = request.POST.get('dark_mode') == 'on'
            profile.save()
        return redirect(f"{request.path}?tab={tab_action}")
        
    notifications = []
    if active_tab == 'thong-bao':
        notifications = Notification.objects.filter(user=request.user)
        
    return render(request, 'caidat.html', {
        'profile': profile,
        'active_tab': active_tab,
        'notifications': notifications,
    })

@login_required
def mark_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})

@login_required
def goicuoc_view(request):
    profile = request.user.userprofile
    return render(request, 'goicuoc.html', {'profile': profile})

@login_required
def change_user_plan(request):
    if request.method == 'POST':
        new_plan = request.POST.get('plan_type')
        profile = request.user.userprofile
        
        if new_plan == 'basic':
            profile.plan = 'basic'
            profile.plan_expiry_date = None
            SecurityLog.objects.create(
                user=request.user, action="Đã hạ cấp về gói Basic", details="", log_type="warning"
            )
        elif new_plan in ['pro', 'premium']:
            profile.plan = new_plan
            profile.plan_expiry_date = timezone.now() + timedelta(days=30)
            SecurityLog.objects.create(
                user=request.user, action=f"Đã nâng cấp lên gói {new_plan.title()} (30 ngày)", details="", log_type="success"
            )
            
        profile.save()
        messages.success(request, 'Cập nhật gói cước thành công!')
    return redirect('goi_cuoc')

def get_recent_files(root_path, limit=4):
    """Hàm quét nông thư mục gốc để lấy các file mới nhất (tránh gây lag)"""
    recent_files = []
    # Khai báo sẵn các chuỗi class màu của Tailwind
    color_classes = {
        'blue': 'text-blue-500 bg-blue-50',
        'purple': 'text-purple-500 bg-purple-50',
        'red': 'text-red-500 bg-red-50',
        'green': 'text-green-500 bg-green-50',
        'yellow': 'text-yellow-600 bg-yellow-50',
        'gray': 'text-gray-500 bg-gray-50',
    }
    
    try:
        # Lấy file từ thư mục gốc của ổ đĩa đang chọn
        with os.scandir(root_path) as entries:
            for entry in entries:
                if entry.is_file(follow_symlinks=False):
                    stat = entry.stat(follow_symlinks=False)
                    ext = os.path.splitext(entry.name)[1].lower()
                    
                    # Tự động nhận diện định dạng file để gán Icon và Màu
                    if ext in ['.doc', '.docx', '.pdf', '.txt']:
                        icon, color = 'file-text', 'blue'
                    elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                        icon, color = 'image', 'purple'
                    elif ext in ['.mp4', '.avi', '.mkv', '.mov']:
                        icon, color = 'video', 'red'
                    elif ext in ['.xls', '.xlsx', '.csv']:
                        icon, color = 'table', 'green'
                    elif ext in ['.zip', '.rar', '.7z']:
                        icon, color = 'archive', 'yellow'
                    else:
                        icon, color = 'file', 'gray'

                    recent_files.append({
                        'name': entry.name,
                        'path': entry.path,
                        'size': round(stat.st_size / (1024 * 1024), 2), # Chuyển ra MB
                        'timestamp': stat.st_mtime,
                        'date': datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%H:%M - %d/%m'),
                        'icon': icon,
                        'color_class': color_classes[color]
                    })
    except Exception:
        pass
    
    # Sắp xếp danh sách ưu tiên file mới nhất và chỉ lấy 4 file đầu tiên
    recent_files.sort(key=lambda x: x['timestamp'], reverse=True)
    return recent_files[:limit]

@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    search_query = request.GET.get('q', '')
    if search_query:
        users = User.objects.filter(username__icontains=search_query).select_related('userprofile')
    else:
        users = User.objects.all().select_related('userprofile').order_by('-id')
    context = {
        'users': users,
        'search_query': search_query,
    }
    return render(request, 'admin_dashboard.html', context)

@user_passes_test(lambda u: u.is_superuser)
def upgrade_premium(request, user_id):
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            plan_type = request.POST.get('plan_type', 'premium')
            duration_days = int(request.POST.get('duration_days', 30))
            
            user.userprofile.plan = plan_type
            user.userprofile.plan_expiry_date = timezone.now() + timedelta(days=duration_days)
            user.userprofile.save()
            
            SecurityLog.objects.create(
                user=user, 
                action=f"Tài khoản được nâng cấp lên {plan_type.upper()} trong {duration_days} ngày", 
                details="", 
                log_type="success"
            )
        except User.DoesNotExist:
            pass
    return redirect('admin_dashboard')

@user_passes_test(lambda u: u.is_superuser)
def downgrade_basic(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        user.userprofile.plan = 'basic'
        user.userprofile.plan_expiry_date = None
        user.userprofile.save()
        SecurityLog.objects.create(
            user=user,
            action="Tài khoản đã bị hạ cấp về gói Basic",
            details="",
            log_type="warning"
        )
    except User.DoesNotExist:
        pass
    return redirect('admin_dashboard')

@user_passes_test(lambda u: u.is_superuser)
def toggle_lock_user(request, user_id):
    if user_id != request.user.id:
        try:
            user = User.objects.get(id=user_id)
            user.is_active = not user.is_active
            user.save()
        except User.DoesNotExist:
            pass
    return redirect('admin_dashboard')

def custom_404(request, exception):
    return render(request, '404.html', status=404)