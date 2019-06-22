from rest_framework import serializers
from .models import DataSource
from .models import DataSourcelLabel
from .models import Excel_Datasource
from .models import WeCourse


class DatasourceSerializer(serializers.ModelSerializer):
    class Meta():
        model = DataSource
        fields = "__all__"


class DatasourceLabelSerializer(serializers.ModelSerializer):
    class Meta():
        model = DataSourcelLabel
        fields = "level", "name", "remark"


class ExcelDatasourceSerializer(serializers.ModelSerializer):
    class Meta():
        model = Excel_Datasource
        fields = '__all__'


class WeCourseSerializer(serializers.ModelSerializer):
    class Meta():
        model = WeCourse
        fields = '__all__'
