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
    path('ky-gui/', views.kygui_view, name='ky-gui'),
    path('cai-dat/', views.caidat_view, name='cai-dat'),
]