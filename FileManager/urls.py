from django.contrib import admin
from django.urls import path
from core.views import dashboard_view # Import hàm vừa viết

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_view, name='trang-chu'), # Để trống '' nghĩa là trang chủ gốc
]