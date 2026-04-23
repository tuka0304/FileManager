from django.contrib import admin
from django.urls import path
from core.views import dashboard_view # Import hàm vừa viết
from core.views import teptin_view # Import hàm vừa viết

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_view, name='trang-chu'),
    path('tep-tin/',teptin_view , name='tep-tin'),  # Để trống '' nghĩa là trang chủ gốc
]