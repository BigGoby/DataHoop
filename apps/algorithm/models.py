from django.db import models
from users.models import UserProfile
from files.models import AlgoLabel, Model_Label


# 算法表
class Algorithms(models.Model):
    name = models.CharField(max_length=128, verbose_name="算法名称")
    user = models.ForeignKey(UserProfile, verbose_name="创建者")
    objid = models.CharField(max_length=128, default='', verbose_name="算法OBJID")
    label = models.ManyToManyField(AlgoLabel, verbose_name="标签")
    is_share = models.IntegerField(choices=((0, '否'), (1, '是')), default=0, verbose_name='是否分享')
    fav_num = models.IntegerField(default=0, verbose_name='收藏次数')
    download_num = models.IntegerField(default=0, verbose_name='下载次数')
    thumb_num = models.IntegerField(default=0, verbose_name='点赞次数')
    view_num = models.IntegerField(default=0, verbose_name='浏览次数')
    type = models.IntegerField(choices=((0, "单机"), (1, "分布式"), (2, "自定义")), default=0, verbose_name="算法类型")
    status = models.IntegerField(choices=((0, '停用'), (1, '启用')), default=1, verbose_name='状态')
    price = models.IntegerField(default=0, verbose_name="价钱/元")
    title = models.CharField(max_length=64, default='', verbose_name="标题")
    abstract = models.TextField(max_length=256, default='', verbose_name="简介")
    add_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "算法表"
        verbose_name_plural = verbose_name

    @property
    def label_name(self):
        return self.label.name


# 模型表
class ModelResult(models.Model):
    """模型表"""
    user = models.ForeignKey(UserProfile, verbose_name="用户名")
    ModelName = models.CharField(max_length=32, verbose_name="模型名")
    OBJID = models.CharField(max_length=128, verbose_name='模型OBJID', default='')
    remark = models.TextField(max_length=512, default='', verbose_name="备注")
    abstract = models.TextField(max_length=256, default='', verbose_name="简介")
    label = models.ManyToManyField(Model_Label, verbose_name="标签")
    fav_num = models.IntegerField(default=0, verbose_name='收藏次数')
    download_num = models.IntegerField(default=0, verbose_name='下载次数')
    thumb_num = models.IntegerField(default=0, verbose_name='点赞次数')
    view_num = models.IntegerField(default=0, verbose_name='浏览次数')
    is_share = models.SmallIntegerField(choices=((0, '是'), (1, "否")), blank=True, null=True, default=1,
                                        verbose_name='是否分享')
    price = models.IntegerField(default=0, verbose_name="价钱/元")
    type = models.IntegerField(choices=((0, "单机"), (1, "分布式")), default=0, verbose_name="是否分布式")
    status = models.IntegerField(choices=((1, '启用'), (2, '停用')), default=1, verbose_name='状态')
    add_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    def __str__(self):
        # 返回模型名
        return self.ModelName

    class Meta:
        verbose_name = "模型表"
        verbose_name_plural = verbose_name

    @property
    def label_name(self):
        return self.label.name


# 算法是否最新
class IsNew(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name="用户名")
    algo_id = models.IntegerField(verbose_name="算法id")
    add_time = models.DateTimeField(auto_now_add=True, verbose_name="插入时间")

    def __int__(self):
        return self.algo_id

    class Meta:
        verbose_name = "算法查看记录"
        verbose_name_plural = verbose_name


class ResourceAllocation(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name="用户名")
    name = models.IntegerField(choices=((0, "计算"), (1, "存储")), default=0, verbose_name="资源名称")
    allocation = models.IntegerField(choices=((0, "小"), (1, "中"), (2, "大")), default=0, verbose_name="资源配置")
    num = models.IntegerField(default=0, verbose_name="资源个数")

    def __int__(self):
        return self.name

    class Meta:
        verbose_name = "资源配置表"
        verbose_name_plural = verbose_name
