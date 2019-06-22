from rest_framework import serializers
from .models import Algorithms, ModelResult
from files.models import AlgoLabel, Model_Label

from users.models import UserProfile


class AlogLabelSerializer(serializers.ModelSerializer):
    """获取算法标签中的信息， 因为是ManyToManyField，所以如此"""

    class Meta:
        model = AlgoLabel
        fields = ('name',)


class UserSerializer(serializers.ModelSerializer):
    """用户表"""

    class Meta:
        model = UserProfile
        fields = ("id", "username", "image")


class AlgIsNew(serializers.IntegerField):
    """ 算法是否最新 """
    isNew = serializers.IntegerField(read_only=True, default='1', label="是否新出")

    def __int__(self):
        self.isNew = ''
        return self.isNew

    class Meta:
        fields = "isNew"


class AlgGetSerializer(serializers.ModelSerializer):
    """
    算法表
    GET : 首页算法的展示和搜索
    """
    user = UserSerializer(label="用户名")
    configuration = serializers.CharField(read_only=True, label="算法配置文件")
    isNew = serializers.IntegerField(read_only=True, default='1', label="是否新出0不是1是")
    trial = serializers.IntegerField(read_only=True, default='1', label="是否试算0不是1是")
    isCollect = serializers.IntegerField(read_only=True, default='1', label="是否收藏0不是1是")
    isLove = serializers.IntegerField(read_only=True, default='1', label="是否喜欢0不是1是")
    isMe = serializers.IntegerField(read_only=True, default='0', label="是否是自己0不是1是")
    label = AlogLabelSerializer(many=True, label="标签")

    class Meta:
        model = Algorithms
        fields = "__all__"
        # fields= ("id","name","user","isNew","label_name")

    def get_value(self, dictionary):
        print(dictionary)
        return dictionary


class AlgFileSerializer(serializers.ModelSerializer):
    """
    算法表
    POST: 算法文件上传+算法参数文件上传
    """
    objid = serializers.FileField(write_only=True, label="算法文件：")
    configuration = serializers.FileField(write_only=True, label="配置文件：")

    # user = serializers.CharField(read_only=True,label="用户名")
    # label = AlogLabelSerializer(many=True,label="标签")

    class Meta:
        model = Algorithms
        fields = "__all__"
        # fields= ("id","name","user","isNew","label_name")


class AlgSerializer(serializers.ModelSerializer):
    """算法表  编写+参数文件上传"""
    # name = serializers.CharField(max_length=128,label="算法名称：")
    # objid = serializers.CharField(label="objid")
    objid = serializers.CharField(write_only=True, label="输入算法")
    configuration = serializers.FileField(write_only=True, label="配置文件：")

    # user = serializers.CharField(read_only=True, label="用户名")
    class Meta:
        model = Algorithms
        fields = "__all__"


class AlgWriteSerializer(serializers.ModelSerializer):
    """算法   编写+参数编写  上传"""
    objid = serializers.CharField(write_only=True, label="输入算法")
    configuration = serializers.CharField(write_only=True, label="配置文件")
    is_share = serializers.IntegerField(read_only=True, label="是否分享")
    fav_num = serializers.IntegerField(read_only=True, label="收藏次数")
    download_num = serializers.IntegerField(read_only=True, label="下载次数")
    thumb_num = serializers.IntegerField(read_only=True, label="点赞次数")
    view_num = serializers.IntegerField(read_only=True, label="浏览次数")
    status = serializers.IntegerField(read_only=True, label="状态")
    price = serializers.IntegerField(read_only=True, label="价钱")

    # user = serializers.CharField(read_only=True, label="用户名")
    class Meta:
        model = Algorithms
        # ("","")
        fields = "__all__"


class AlgModelGetSerializer(serializers.ModelSerializer):
    """算法   编写+参数编写  上传"""
    user = UserSerializer(label="用户名")

    class Meta:
        model = Algorithms
        fields = "__all__"


from files.models import DataSource


class DataSourceSerializer(serializers.ModelSerializer):
    """数据源表"""
    file_name = serializers.CharField(read_only=True)

    class Meta:
        model = DataSource
        fields = ("id", "file_name", "obj_id", "where", "format_filename", "title")


class ModelLabelSerializer(serializers.ModelSerializer):
    """获取模型标签中的信息， 因为是ManyToManyField，所以如此"""

    class Meta:
        model = Model_Label
        fields = ('name', 'type')


class ModelResultSerializer(serializers.ModelSerializer):
    """数据源表 get """
    OBJID = serializers.CharField(label="模型")
    label = ModelLabelSerializer(read_only=True, many=True, label="标签")

    class Meta:
        model = ModelResult
        fields = "__all__"


class ModelResultSerializer2(serializers.ModelSerializer):
    """数据源表 post """
    OBJID = serializers.CharField(label="OBJID")
    moduleData = serializers.CharField(write_only=True, label="模型数据")

    class Meta:
        model = ModelResult
        fields = ("id", "user", "OBJID", "ModelName", "remark", "moduleData", "label")


class GetModelLabelSerializer(serializers.ModelSerializer):
    """模型标签表"""

    class Meta:
        model = Model_Label
        fields = "__all__"


class GetAlgoLabelSerializer(serializers.ModelSerializer):
    """算法标签表"""

    class Meta:
        model = AlgoLabel
        fields = "__all__"
