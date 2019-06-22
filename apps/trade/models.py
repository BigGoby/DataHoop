from django.db import models
from users.models import UserProfile


# Create your models here.
# 项目中心表
class ProjectCenter(models.Model):
    PROJECT_TYPE = (
        (1, "商业"),
        (2, "文化"),
        (3, "环境"),
        (4, "生活"),
        (5, "社会"),
        (6, "体育"),
        (7, "教育"),
        (8, "科技"),
        (9, "时政"),
    )
    user = models.ForeignKey(UserProfile, verbose_name="所属用户")
    name = models.CharField(max_length=100, verbose_name='项目名称', null=True, blank=True)
    status = models.CharField(max_length=32, verbose_name='状态', default='进行中')
    organizers = models.CharField(max_length=100, verbose_name='举办方', null=True, blank=True)
    money = models.FloatField(verbose_name="奖金", default=0)
    details = models.TextField(verbose_name='简介', null=True, blank=True)
    area = models.CharField(max_length=32, verbose_name='项目发布地区', null=True, blank=True)
    pro_type = models.CharField(max_length=32, verbose_name='项目资源分类', default='')
    labels = models.IntegerField(choices=PROJECT_TYPE, verbose_name="分类", default=1)
    count = models.IntegerField(verbose_name='竞标人数', default=0)
    pledge = models.FloatField(verbose_name="项目押金", default=0)
    key_word = models.CharField(max_length=32, verbose_name='项目关键词', null=True, blank=True)
    click_num = models.IntegerField(verbose_name='点击量', default=0)
    end_time = models.DateField(auto_now_add=True, verbose_name="项目竞标截止时间")
    publish_time = models.DateTimeField(auto_now_add=True, verbose_name='项目发布时间')
    finish_time = models.CharField(max_length=32, verbose_name='项目预计工期', null=True, blank=True)
    technology = models.CharField(max_length=100, verbose_name='技术要求', null=True, blank=True)
    standard = models.CharField(max_length=225, verbose_name='完成标准', null=True, blank=True)
    attention = models.TextField(verbose_name='注意事项', null=True, blank=True)
    download = models.TextField(verbose_name='数据说明及下载链接', null=True, blank=True)

    add_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")

    del_time = models.DateTimeField(auto_now=True, verbose_name="移除时间")
    is_top = models.IntegerField(choices=(
        (0, '非置顶'),
        (1, '置顶')
    ), verbose_name='项目是否置顶', default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '项目中心'
        verbose_name_plural = verbose_name


# 项目竞标
class BidDetails(models.Model):
    project = models.ForeignKey(ProjectCenter, verbose_name='所属项目', related_name='project_bid')
    user = models.ForeignKey(UserProfile, verbose_name="竞标人")
    bid_time = models.DateTimeField(auto_now_add=True, verbose_name="竞标时间")
    bid_price = models.CharField(max_length=32, verbose_name="竞标价格", null=True, blank=True)
    end_time = models.CharField(max_length=32, verbose_name="项目完成工期", null=True, blank=True)
    remark = models.TextField(verbose_name="留言", null=True, blank=True)
    contact = models.CharField(max_length=32, verbose_name="联系方式", null=True, blank=True)
    select = models.BooleanField(default=False, verbose_name="是否选择")
    ensure = models.BooleanField(default=False, verbose_name="确认选择")
    inform = models.IntegerField(choices=((0, '未读'), (1, '已读')), default=0, verbose_name='竞标通知')
    add_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")

    def __str__(self):
        return self.project.name

    class Meta:
        verbose_name = '竞标详情'
        verbose_name_plural = verbose_name
        unique_together = ('project', 'user')
