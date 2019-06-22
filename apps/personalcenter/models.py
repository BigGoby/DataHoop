import math

from files.models import UserProfile
from files.models import WeCourse
from django.db import models
from DjangoUeditor.models import UEditorField


class Relationship(models.Model):
    name = 'Relationship'
    author = models.ForeignKey(UserProfile, verbose_name="作者", default='')
    Re_Status = models.IntegerField(choices=((0, '未关注'), (1, '已关注')), default=0, verbose_name='对方是否关注我')
    User_ByID = models.CharField(max_length=32, null=False, verbose_name='被关注用户的ＩＤ')

    def __str__(self):
        return self.User_ByID

    class Meta:
        verbose_name_plural = "用户关系表"


class Sign(models.Model):
    name = 'Sign'
    author = models.ForeignKey(UserProfile, verbose_name="作者", default='')
    Sign_Time = models.DateTimeField(auto_now=True, verbose_name='签到时间')
    days = models.IntegerField(default='0', verbose_name='签到天数')

    def __str__(self):
        return self.author.phone

    class Meta:
        verbose_name_plural = '签到表'


class MyNote(models.Model):
    name = 'MyNote'
    author = models.ForeignKey(UserProfile, verbose_name="作者", default='')
    title = models.CharField(max_length=50, verbose_name="标题", default='')
    content = UEditorField(imagePath="note/images/", width=843.66, height=300,
                           filePath="note/files/", default='', verbose_name='文本编辑器')
    date = models.DateField(auto_now_add=True, verbose_name='創建日期')
    share_status = models.IntegerField(choices=((0, '已共享'), (1, '未共享')), default=1, verbose_name='共享状态')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = '个人笔记'


class Myscore(models.Model):
    name = 'Myscore'
    author = models.ForeignKey(UserProfile, verbose_name="作者", default='')
    Score = models.IntegerField(null=False, verbose_name='积分值', default=0)
    In_Score = models.IntegerField(null=True, verbose_name='积分收入', default=0)
    Out_Score = models.IntegerField(null=True, verbose_name='积分指出', default=0)
    ScoreInfo = models.TextField(verbose_name='积分说明', default='scoreinfo')

    def __str__(self):
        return self.ScoreInfo

    def get_level(self):
        return int(math.sqrt(self.Score + 4) - 1)

    class Meta:
        verbose_name_plural = '积分详情'


class Collect(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name='所有者')
    file_id = models.IntegerField(verbose_name='文件id')
    source = models.IntegerField(choices=((1, 'datasource'), (2, 'algorithm'), (3, 'model')), default=1,
                                 verbose_name='来源')
    add_time = models.DateTimeField(auto_now=True, verbose_name='收藏时间')

    def __int__(self):
        return self.file_id

    class Meta:
        verbose_name_plural = '收藏'


class Love(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name='所有者')
    file_id = models.IntegerField(verbose_name='文件id')
    source = models.IntegerField(choices=((1, 'datasource'), (2, 'algorithm'), (3, 'model'), (4, 'wesourse')),
                                 default=1, verbose_name='来源')
    add_time = models.DateTimeField(auto_now=True, verbose_name='收藏时间')

    def __int__(self):
        return self.file_id

    class Meta:
        verbose_name_plural = '喜欢'


class MyCourse(models.Model):
    """
    我购买的课程
    """
    student = models.ForeignKey(UserProfile, verbose_name='购买者')
    course = models.ForeignKey(WeCourse, verbose_name='购买课程')
    time = models.DateTimeField(auto_now=True, verbose_name='购买时间')

    def __str__(self):
        return self.course.name

    class Meta:
        verbose_name = '我的课程'
        verbose_name_plural = verbose_name


class UserFellBack(models.Model):
    '''
    用户反馈
    '''
    title = models.CharField(max_length=100, default='', verbose_name='标题')
    content = models.TextField(max_length=600, default='', verbose_name='反馈内容')
    contact = models.CharField(max_length=50, default='', verbose_name='联系方式')
    add_time = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = '用户反馈'
        verbose_name_plural = verbose_name


class OperationSettings(models.Model):
    '''运营设置：会员等级，存储空间，犀秒，价格设定，折扣设定'''
    level = models.IntegerField(choices=((1, "注册会员"), (2, "铜牌会员"), (3, "银牌会员"), (4, "金牌会员"),
                                         (5, '钻石会员')), default=1, unique=True, verbose_name='会员等级')
    expenditure = models.FloatField(default=0, verbose_name='花费')
    storage = models.IntegerField(default=20, verbose_name='存储空间（MB）')
    storage_price = models.FloatField(default=1, verbose_name='存储价格（元/GB/月）')
    storage_discount_m = models.FloatField(default=0.95, verbose_name='存储折扣/月')
    storage_discount_y = models.FloatField(default=0.9, verbose_name='存储折扣/年')
    score = models.IntegerField(default=0, verbose_name='积分')
    rhino_s = models.IntegerField(default=0, verbose_name='犀秒')
    rhino_s_price = models.FloatField(default=0.1, verbose_name='犀秒价格（元/秒）')
    rhino_s_discount = models.FloatField(default=0.95, verbose_name='犀秒折扣')
    time = models.DateTimeField(auto_now_add=True, verbose_name='设置时间')

    def __int__(self):
        return self.level

    class Meta:
        verbose_name = '会员等级设置'
        verbose_name_plural = verbose_name
