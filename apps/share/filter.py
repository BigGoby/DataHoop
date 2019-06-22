import django_filters

from files.models import DataSource
from algorithm.models import Algorithms, ModelResult


class DataSourceFilter(django_filters.rest_framework.FilterSet):
    """
    自定义过滤类
    """
    parent = django_filters.NumberFilter(name='parent')
    share_status = django_filters.NumberFilter(name='share_status')

    # tag = django_filters.CharFilter(name='tag')

    class Meta:
        model = DataSource
        fields = ['parent', 'share_status']


class AlgorithmsFilter(django_filters.rest_framework.FilterSet):
    """
    自定义过滤类
    """
    # label = django_filters.CharFilter(name='label')
    # tag = django_filters.CharFilter(name='tag')
    share_status = django_filters.NumberFilter(name='share_status')

    class Meta:
        model = Algorithms
        fields = ['share_status']


class ModelResultFilter(django_filters.rest_framework.FilterSet):
    """
    自定义过滤类
    """
    # label = django_filters.CharFilter(name='label')
    # tag = django_filters.CharFilter(name='tag')
    share_status = django_filters.NumberFilter(name='share_status')

    class Meta:
        model = ModelResult
        fields = ['share_status']
