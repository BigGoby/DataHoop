from django.db import models

# Create your models here.


class Community(models.Model):
    title = models.CharField(max_length=50, verbose_name='标题')
    file = models.ImageField(upload_to='community/QRcode', verbose_name='微信二维码')
    add_time = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')
