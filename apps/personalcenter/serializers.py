from rest_framework import serializers
from users.models import UserProfile
from .models import MyCourse
from files.models import WeCourse
from algorithm.models import AlgoLabel, Algorithms


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta():
        model = UserProfile
        fields = "__all__"


class WeCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeCourse
        fields = ["name", ]


class MyCourseSerializer(serializers.ModelSerializer):
    course = WeCourseSerializer()

    class Meta():
        model = MyCourse
        fields = "__all__"


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
