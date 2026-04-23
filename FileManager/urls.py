from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core.views import dashboard_view, register_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_view, name='trang-chu'),

    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/register/', register_view, name='register'),

    path('accounts/password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('accounts/password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]