from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class FormDangKyTuyChinh(UserCreationForm):
    # Ép buộc người dùng phải nhập email
    email = forms.EmailField(required=True, label="Địa chỉ Email")

    class Meta(UserCreationForm.Meta):
        model = User
        # Hiển thị các trường: tên đăng nhập, email, và 2 lần mật khẩu
        fields = UserCreationForm.Meta.fields + ('email',)