import django_filters
from .models import Info


class NewsFilter(django_filters.rest_framework.FilterSet):
    """
    自定义过滤类
    """
    label = django_filters.NumberFilter(name='label')

    class Meta:
        model = Info
        fields = ['label']
