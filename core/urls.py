from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Hệ thống tự xử lý Đăng nhập, Đăng xuất, Quên MK
    path('dang-nhap/', auth_views.LoginView.as_view(template_name='dangnhap.html'), name='login'),
    path('dang-xuat/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('quen-mat-khau/', auth_views.PasswordResetView.as_view(template_name='quenmk.html'), name='password_reset'),
    
    # Các trang hệ thống (Đã đồng bộ tên chuẩn xác)
    path('dang-ky/', views.register_view, name='register'),
    path('', views.dashboard_view, name='trang-chu'),
    path('tep-tin/', views.teptin_view, name='tep-tin'),
    path('quet-don/', views.quetdon_view, name='quet-don'),
    path('xoa-tep/', views.delete_scanned_item, name='delete_scanned_item'),
    path('chuyen-file/', views.chuyenfile_view, name='chuyen-file'),
    path('bao-mat/', views.baomat_view, name='bao-mat'),
    path('bao-mat/scan/', views.scan_security, name='scan_security'),
    path('bao-mat/toggle-network/', views.toggle_network_security, name='toggle_network'),
    path('ky-gui/', views.kygui_view, name='ky-gui'),
    path('ky-gui/unlock/', views.unlock_vault, name='unlock_vault'),
    path('ky-gui/lock/', views.lock_vault, name='lock_vault'),
    path('ky-gui/download/<str:file_id>/', views.download_vault_file, name='download_vault'),
    path('cai-dat/', views.caidat_view, name='cai-dat'),
    path('goi-cuoc/', views.goicuoc_view, name='goi_cuoc'),
    path('goi-cuoc/change/', views.change_user_plan, name='change_user_plan'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/upgrade/<int:user_id>/', views.upgrade_premium, name='admin_upgrade'),
    path('admin-panel/downgrade/<int:user_id>/', views.downgrade_basic, name='admin_downgrade'),
    path('admin-panel/lock/<int:user_id>/', views.toggle_lock_user, name='admin_lock'),
]