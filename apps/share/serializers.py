from rest_framework import serializers
from files.models import DataSource
from algorithm.models import Algorithms, ModelResult


# 共享数据
class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = "__all__"


# 共享算法
class AlgorithmsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Algorithms
        fields = "__all__"


# 共享模型
class ModelResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelResult
        fields = "__all__"
