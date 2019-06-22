from django.db import models
from users.models import UserProfile
from DjangoUeditor.models import UEditorField


class DataSource(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name="作者ID")
    file_name = models.FileField(blank=False, null=False, verbose_name="文件名")
    format_filename = models.CharField(max_length=64, blank=True, verbose_name="格式化文件名")
    share_status = models.IntegerField(choices=((0, '公有'), (1, '私有')), default=1, verbose_name='共享状态')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="文件上传时间")
    fileSize = models.CharField(max_length=32, default='', verbose_name='文件大小')
    obj_id = models.CharField(max_length=64, blank=True, default='', verbose_name='mongo_objID')
    row_num = models.IntegerField(default=0, verbose_name='文件行数', )
    column_num = models.IntegerField(default=0, verbose_name='文件列数')
    download_num = models.IntegerField(default=0, verbose_name='文件下载次数')
    fav_num = models.IntegerField(default=0, verbose_name='收藏次数')
    view_num = models.IntegerField(default=0, verbose_name='文件浏览次数')
    thumb_num = models.IntegerField(default=0, verbose_name='文件点赞次数')
    title = models.CharField(max_length=1024, default='', verbose_name='表头')
    price = models.FloatField(default=0, verbose_name='数据价格')
    where = models.CharField(default='', max_length=12, verbose_name='存储介质')
    column_delimiter = models.CharField(default=',', max_length=6, verbose_name='列分隔符')
    row_delimiter = models.CharField(default='/n', max_length=6, verbose_name='行分隔符')
    is_header = models.IntegerField(default='1', choices=((0, 'no'), (1, 'yes')), verbose_name='是否包含表头')
    detail = models.TextField(verbose_name='字段类型', default='', blank=True)
    category = models.IntegerField(choices=((1, '数据'),
                                            (2, '算法'),
                                            (3, '模型')), default=1,
                                   verbose_name='类别')
    parent = models.IntegerField(choices=((1, "商业"),
                                          (2, "文化"),
                                          (3, "环境"),
                                          (4, "生活"),
                                          (5, "社会"),
                                          (6, "体育"),
                                          (7, "教育"),
                                          (8, "科技"),
                                          (9, "时政")), default=1,
                                 verbose_name='分类')
    label_name = models.CharField(default='', max_length=50, verbose_name='标签名称')

    def __str__(self):
        return self.format_filename

    class Meta:
        verbose_name_plural = "数据源"


class DataSourcelLabel(models.Model):
    name = models.CharField(max_length=50, verbose_name='标签名称')
    parent = models.IntegerField(choices=((1, "商业"),
                                          (2, "文化"),
                                          (3, "环境"),
                                          (4, "生活"),
                                          (5, "社会"),
                                          (6, "体育"),
                                          (7, "教育"),
                                          (8, "科技"),
                                          (9, "时政")), default=1,
                                 verbose_name='分类')

    weight = models.IntegerField(default=0, verbose_name='标准权重')
    opweight = models.IntegerField(default=0, verbose_name='运营权重')
    remark = models.CharField(max_length=128, default='', verbose_name='备注')
    status = models.IntegerField(choices=((0, '已停用'), (1, '启用')), default=1, verbose_name='状态')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '数据源标签'


class UserLabel(models.Model):
    name = models.CharField(max_length=50, verbose_name='标签名称')
    level = models.IntegerField(choices=((1, '一级标签'), (2, '二级标签')), verbose_name='标签等级')
    parent = models.ForeignKey('self', null=True, blank=True, related_name='kid', verbose_name='父类标签')
    contribution_rate = models.IntegerField(default=0, verbose_name='贡献率')
    weight = models.IntegerField(default=0, verbose_name='标准权重')
    opweight = models.IntegerField(default=0, verbose_name='运营权重')
    remark = models.CharField(max_length=128, default='', verbose_name='备注')
    status = models.IntegerField(choices=((0, '已停用'), (1, '启用')), default=1, verbose_name='状态')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '用户标签'


class UserToLabel(models.Model):
    user = models.ForeignKey(UserProfile, null=True, blank=True, verbose_name='用户')
    label = models.ForeignKey(UserLabel, null=True, blank=True, verbose_name='用户标签')

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name_plural = '用户标签1'


class AlgoLabel(models.Model):
    type = models.IntegerField(choices=((1, 'languange'),
                                        (2, 'func'),
                                        (3, 'type')), default=1, verbose_name="类型")
    name = models.CharField(max_length=50, verbose_name='一级标签名称')
    second_name = models.CharField(max_length=50, default='', verbose_name='二级标签名称')
    weight = models.IntegerField(default=1, verbose_name='标准权重')
    opweight = models.IntegerField(default=1, verbose_name='运营权重')

    remark = models.CharField(max_length=128, default='', verbose_name='备注')
    status = models.IntegerField(choices=((0, '已停用'), (1, '启用')), default=1, verbose_name='状态')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '算法标签'


class Model_Label(models.Model):
    type = models.IntegerField(choices=((1, 'languange'),
                                        (2, 'func'),
                                        (3, 'type')), default=1, verbose_name="类型")
    name = models.CharField(max_length=50, verbose_name='一级标签名称')
    second_name = models.CharField(max_length=50, default='', verbose_name='二级标签名称')
    weight = models.IntegerField(default=1, verbose_name='标准权重')
    opweight = models.IntegerField(default=1, verbose_name='运营权重')

    remark = models.CharField(max_length=128, default='', verbose_name='备注')
    status = models.IntegerField(choices=((0, '已停用'), (1, '启用')), default=1, verbose_name='状态')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '模型标签'


class StorageLabel(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name='用户')
    storage = models.IntegerField(verbose_name='存储', choices=((1, 'M'), (2, 'G'), (3, 'T'), (4, 'P')), default=1)
    name = models.CharField(max_length=50, verbose_name='标签名称')
    level = models.IntegerField(choices=((1, '一级标签'), (2, '二级标签')), verbose_name='标签等级')
    parent = models.ForeignKey('self', null=True, blank=True, related_name='kid', verbose_name='父类标签')
    weight = models.IntegerField(default=0, verbose_name='标准权重')
    type = models.IntegerField(default=1, verbose_name='类型')
    opweight = models.IntegerField(default=0, verbose_name='运营权重')
    remark = models.CharField(max_length=128, default='', verbose_name='备注')
    status = models.IntegerField(choices=((0, '已停用'), (1, '启用')), default=1, verbose_name='状态')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '存储标签'


class Association(models.Model):
    name = models.CharField(max_length=50, verbose_name='标签名称')
    level = models.IntegerField(choices=((1, '一级标签'), (2, '二级标签')), verbose_name='标签等级')
    parent = models.ForeignKey('self', null=True, blank=True, related_name='kid', verbose_name='父类标签')
    weight = models.IntegerField(default=0, verbose_name='标准权重')
    opweight = models.IntegerField(default=0, verbose_name='运营权重')
    remark = models.CharField(max_length=128, default='', verbose_name='备注')
    status = models.IntegerField(choices=((0, '已停用'), (1, '启用')), default=1, verbose_name='状态')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '社群标签'


class Excel_Datasource(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name="作者ID")
    file_name = models.FileField(blank=False, null=False, verbose_name="文件名")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="文件上传时间")

    def __str__(self):
        return self.file_name

    class Meta:
        verbose_name = '上传标签'
        verbose_name_plural = verbose_name


class WeCourse(models.Model):
    # 微课
    user = models.ForeignKey(UserProfile, default=1, verbose_name='创建者')
    name = models.CharField(max_length=128, verbose_name="课程名称")
    label = models.CharField(max_length=128, null=True, blank=True, verbose_name="课程标签")
    abstract = models.TextField(max_length=256, default='', blank=True, verbose_name="简介")
    content = UEditorField(imagePath="files/images/", width=843.66, height=300,
                           filePath="files/files/", default='', blank=True, verbose_name='文本编辑器')
    cover = models.ImageField(upload_to="files/cover/", default='', blank=True, verbose_name='封面')
    main_push = models.IntegerField(choices=((1, "一级"), (2, "二级"), (3, "三级")), default=1, verbose_name="主推等级")
    view_num = models.IntegerField(default=0, verbose_name='课程浏览次数')
    thumb_num = models.IntegerField(default=0, verbose_name='课程点赞次数')
    is_buy = models.BooleanField(choices=((0, "否"), (1, "是")), default=0, verbose_name="是否购买")
    price = models.FloatField(default=0, verbose_name='课程价格')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "微课"
        verbose_name_plural = verbose_name
