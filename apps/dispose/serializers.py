from rest_framework import serializers
from files.models import DataSource


# 文件库
class DatasourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = ("file_name",)
