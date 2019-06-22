from django.db import models
from DjangoUeditor.models import UEditorField
from users.models import UserProfile


class Info(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name='作者')
    title = models.CharField(max_length=100, default='', verbose_name='文章标题')
    click_num = models.IntegerField(default=0, verbose_name='点击量')
    add_time = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')
    content = UEditorField(imagePath="news/images/", width=843.66, height=300,
                           filePath="news/files/", default='', verbose_name='文本编辑器')
    desc = models.TextField(default='', verbose_name='文章简介')
    label = models.IntegerField(choices=((1, '综合资讯'), (2, '软件资讯')), default=1, verbose_name='咨询分类')
    cover = models.ImageField(upload_to="news/cover/", default='', verbose_name='封面')
    source = models.CharField(max_length=60, verbose_name='来源', default='')
    author = models.CharField(max_length=20, verbose_name='作者', default='')
    editor = models.CharField(max_length=20, verbose_name='编辑', default='')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = '资讯'
        verbose_name_plural = verbose_name
