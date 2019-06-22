from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.

class UserProfile(AbstractUser):
    """
    用户表
    """
    GLORY = (
        (1, '初级'),
        (2, '中级'),
        (3, '高级'),
    )
    mobile = models.CharField(max_length=11, blank=True, null=True, unique=True,
                              error_messages={
                                  'unique': '该手机号已存在。'
                              },
                              verbose_name='手机号')
    sex = models.CharField(max_length=6, verbose_name='性别', default='男')
    name = models.CharField(max_length=12, verbose_name='姓名', default='')
    detail = models.TextField(verbose_name='个人介绍', default='')
    province = models.CharField(max_length=12, verbose_name='省', default='北京')
    city = models.CharField(max_length=12, verbose_name='市', default='东城')
    industy = models.CharField(max_length=24, verbose_name='行业', default='')
    job = models.CharField(max_length=12, verbose_name='职位', default='')
    company = models.CharField(max_length=255, verbose_name='公司', default='')
    image = models.ImageField(upload_to='image', max_length=225, verbose_name='头像', default='image/default.jpg')
    glory = models.IntegerField(choices=GLORY, default=1, verbose_name='积分等級')
    member_level = models.IntegerField(choices=((1, "注册会员"), (2, "铜牌会员"), (3, "银牌会员"), (4, "金牌会员"),
                                                (5, '钻石会员')), default=1, verbose_name='会员等级')
    origin = models.IntegerField(choices=((1, '网站注册'), (2, 'CRM')), default=1, verbose_name='用户来源')
    money = models.FloatField(default=0, verbose_name='账户余额')
    consume = models.FloatField(default=0, verbose_name='消费总额')
    bind_money = models.FloatField(default=1000, verbose_name='绑定金额')
    # level = models.ForeignKey(UserLevel, null=True, blank=True, verbose_name='vip等级') #之前关联存在问题，暂时去掉
    chaox = models.CharField(max_length=100, null=True, blank=True, verbose_name='超星账号')

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = verbose_name


class UserLevel(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name="用户")  # 根据不同的用户设置不同的权限
    name = models.CharField(max_length=50, verbose_name='权限名称')
    core = models.CharField(max_length=50, verbose_name='核数')
    ram = models.CharField(max_length=50, verbose_name='内存')
    memory = models.CharField(max_length=50, verbose_name='容量')
    up_load = models.IntegerField(verbose_name='上传限制')  # 普通注册会员默认20M
    csv = models.BooleanField(default=False, verbose_name='csv')
    txt = models.BooleanField(default=False, verbose_name='txt')
    sql = models.BooleanField(default=False, verbose_name='sql')
    mySQL = models.BooleanField(default=False, verbose_name='mySQL')
    postgreSQL = models.BooleanField(default=False, verbose_name='postgreSQL')
    SQLsever = models.BooleanField(default=False, verbose_name='SQLsever')
    sol_data = models.BooleanField(default=False, verbose_name='sol-data')
    octopus = models.BooleanField(default=False, verbose_name='八爪鱼')
    delete = models.BooleanField(default=False, verbose_name='删除列')
    # diyfill = models.BooleanField(verbose_name='重命名列')
    diyfill = models.BooleanField(default=False, verbose_name='编辑单元格')
    f_upper = models.BooleanField(default=False, verbose_name='首字母大写')
    upper = models.BooleanField(default=False, verbose_name='全大写')
    letter = models.BooleanField(default=False, verbose_name='全小写')
    union = models.BooleanField(default=False, verbose_name='多表合并')
    textclassify = models.BooleanField(default=False, verbose_name='文本归类')
    prevfill = models.BooleanField(default=False, verbose_name='向前填充')
    netxfill = models.BooleanField(default=False, verbose_name='向后填充')
    de_value = models.BooleanField(default=False, verbose_name='去除缺失值')
    outliers = models.BooleanField(default=False, verbose_name='异常值处理')
    scaler = models.BooleanField(default=False, verbose_name='标准化')
    PCA = models.BooleanField(default=False, verbose_name='降维-主成分分析')
    FA = models.BooleanField(default=False, verbose_name='降维-因子分析')
    onegotencode = models.BooleanField(default=False, verbose_name='编码-独热编码')
    labelencode = models.BooleanField(default=False, verbose_name='编码-标签编码')
    discretization = models.BooleanField(default=False, verbose_name='变量离散化')
    polynomial = models.BooleanField(default=False, verbose_name='多项式特征')
    histogram = models.BooleanField(default=False, verbose_name='柱状图')
    pie = models.BooleanField(default=False, verbose_name='饼图')
    scatter = models.BooleanField(default=False, verbose_name='散点图')
    bar = models.BooleanField(default=False, verbose_name='条柱图')
    brokenline = models.BooleanField(default=False, verbose_name='折线图')
    radar = models.BooleanField(default=False, verbose_name='雷达图')
    heatmap = models.BooleanField(default=False, verbose_name='热力图')
    bubble = models.BooleanField(default=False, verbose_name='气泡图')
    funnel = models.BooleanField(default=False, verbose_name='漏斗图')
    algorithms = models.BooleanField(default=False, verbose_name='模型搭建-算法')

    def __int__(self):
        return self.user

    class Meta:
        verbose_name = '用户权限'
        verbose_name_plural = verbose_name


class VerifyCode(models.Model):
    '''
    短信验证码
    '''
    code = models.CharField(max_length=6, verbose_name='验证码')
    mobile = models.CharField(max_length=11, verbose_name='手机号')
    type = models.IntegerField(choices=((1, '账号注册'),
                                        (2, '忘记密码')), verbose_name='用途')
    add_time = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')

    class Meta:
        verbose_name = '短信验证码'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.code
