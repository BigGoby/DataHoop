from rest_framework import serializers
from .models import ProjectCenter, BidDetails
from users.models import UserProfile


# 项目中心
class ProjectCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCenter
        fields = "__all__"


# 竞标
class BidDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BidDetails
        fields = "__all__"
