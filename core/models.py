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