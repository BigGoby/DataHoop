from django.db import models
from django.utils import timezone
from users.models import UserProfile


class SharingFile(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name='用户', default='')
    title = models.CharField(max_length=100, verbose_name='标题')
    desc = models.CharField(max_length=100, default='', verbose_name='简介')
    content = models.TextField(verbose_name='页面文本')
    source = models.CharField(max_length=50, verbose_name='来源')
    create_time = models.DateTimeField(default=timezone.now, verbose_name='上传时间')
    views_num = models.IntegerField(default=0, verbose_name='浏览量')
    thumb_num = models.IntegerField(default=0, verbose_name='点赞数')
    download_num = models.IntegerField(default=0, verbose_name='下载数')
    # comment_num = models.IntegerField(default=0, verbose_name='评论数')
    collect_num = models.IntegerField(default=0, verbose_name='收藏数')
    score = models.IntegerField(default=0, verbose_name='兑换所需金额')
    label = models.CharField(max_length=100, blank=True, null=True, verbose_name='标签')
    category = models.IntegerField(choices=((1, '数据'),
                                            (2, '算法'),
                                            (3, '模型')),
                                   verbose_name='类别')
    tag = models.IntegerField(choices=((1, "商业"),
                                       (2, "文化"),
                                       (3, "环境"),
                                       (4, "生活"),
                                       (5, "社会"),
                                       (6, "体育"),
                                       (7, "教育"),
                                       (8, "科技"),
                                       (9, "时政")),
                              verbose_name='分类')

    img = models.ImageField(upload_to='image', max_length=100, verbose_name='配图', default='image/default.png')

    class Meta:
        verbose_name = '共享文件'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


class SharingThumb(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name='用户')
    sharingfile = models.ForeignKey(SharingFile, verbose_name='文件')
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')
    type = models.IntegerField(choices=((0, '未读'), (1, '已读')), default=0, verbose_name='点赞状态')

    class Meta:
        verbose_name = '共享文件点赞'
        verbose_name_plural = verbose_name


# class SharingComment(models.Model):
#     user = models.ForeignKey(UserProfile, verbose_name='用户')
#     sharingfile = models.ForeignKey(SharingFile, verbose_name='文件')
#     comment = models.CharField(max_length=200, verbose_name='评论')
#     add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')
#     target = models.CharField(max_length=20, verbose_name='回复用户id', blank=True, null=True)
#     type = models.IntegerField(choices=((0, '未读'), (1, '已读')), default=0, verbose_name='评论状态')
#
#     class Meta:
#         verbose_name = '共享文件评论'
#         verbose_name_plural = verbose_name


class SharingCollect(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name='用户')
    sharingfile = models.ForeignKey(SharingFile, verbose_name='文件')
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '共享文件收藏'
        verbose_name_plural = verbose_name


class SharingConsume(models.Model):
    SOURCE_TYPE = (
        (1, "收入"),
        (2, "支出"),
        (3, "赠送"),
    )
    STATE_TYPE = (
        (1, '已付款'),
        (2, '未付款'),
        (3, '已取消'),
    )
    user = models.ForeignKey(UserProfile, verbose_name='用户')
    sharingfile = models.ForeignKey(SharingFile, verbose_name='文件')
    income = models.FloatField(default=0, verbose_name='收入')
    out = models.FloatField(default=0, verbose_name='支出')
    which = models.IntegerField(choices=((1, '数据'), (2, '算法'), (3, '模型')), default=1, verbose_name='来源')
    state = models.IntegerField(choices=STATE_TYPE, default=1, verbose_name='支付状态')
    source = models.IntegerField(choices=SOURCE_TYPE, default=1, verbose_name='消费类别')
    add_time = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')

    class Meta:
        verbose_name = '共享文件消费'
        verbose_name_plural = verbose_name
