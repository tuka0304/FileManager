import random
from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import render



def dashboard_view(request):
    return render(request, 'dashboard.html')
class KieuGiai(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) # Người sở hữu file
    ten_file = models.CharField(max_length=255)
    kich_thuoc = models.BigIntegerField() # Dung lượng (Bytes)
    ma_bam = models.CharField(max_length=128) # Mã Hash (MD5 hoặc SHA-256) để chống trùng lặp
    drive_file_id = models.CharField(max_length=100) # ID của file trên Google Drive
    ngay_tai_len = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ten_file
    
from django.db import models
from django.contrib.auth.models import User

# 1. Mở rộng thông tin Người dùng (Cho trang Cài đặt)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    job_role = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.user.username

# 2. Lịch sử Chuyển tệp nhanh
class TransferHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    device_name = models.CharField(max_length=100)
    status = models.CharField(max_length=50) # VD: Hoàn tất, Đang xử lý
    file_size = models.CharField(max_length=50) # VD: 2.4 GB
    created_at = models.DateTimeField(auto_now_add=True)
    is_incoming = models.BooleanField(default=False) # Nhận hay Gửi

    def __str__(self):
        return f"{self.file_name} - {self.status}"

# 3. Két sắt bảo mật (Ký gửi an toàn)
class SecuredVault(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=1000)
    file_size = models.CharField(max_length=50)
    is_locked = models.BooleanField(default=True)
    secured_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name

# 4. Chia sẻ tệp nhanh bằng mã PIN
class QuickShare(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='quick_shares/')
    file_name = models.CharField(max_length=255)
    file_size = models.FloatField()
    pin_code = models.CharField(max_length=6, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pin_code:
            while True:
                pin = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                if not QuickShare.objects.filter(pin_code=pin).exists():
                    self.pin_code = pin
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pin_code} - {self.file_name}"

# 5. Lịch sử nhận tệp
class ReceiveHistory(models.Model):
    receiver = models.ForeignKey(User, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    file_size = models.FloatField()
    pin_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.receiver.username} received {self.file_name}"

# 6. Thông báo
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"