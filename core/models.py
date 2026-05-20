import random
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
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
    PLAN_CHOICES = [
        ('basic', 'Basic (Miễn phí)'),
        ('pro', 'Pro (49.000đ/tháng)'),
        ('premium', 'Premium (99.000đ/tháng)'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', default='default_avatar.png')
    auto_deep_scan = models.BooleanField(default=False)
    dark_mode = models.BooleanField(default=False)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='basic')
    plan_expiry_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username

    @property
    def unread_count(self):
        return self.user.notification_set.filter(is_read=False).count()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

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
    drive_file_id = models.CharField(max_length=150)
    file_name = models.CharField(max_length=255)
    file_size = models.FloatField()
    pin_code = models.CharField(max_length=10, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pin_code:
            while True:
                pin = str(random.randint(0, 9999999999)).zfill(10)
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
    pin_code = models.CharField(max_length=10)
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

# 7. Nhật ký hoạt động bảo mật
class SecurityLog(models.Model):
    LOG_TYPES = (
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('info', 'Info'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    details = models.CharField(max_length=255, blank=True)
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.log_type.upper()}] {self.user.username} - {self.action}"