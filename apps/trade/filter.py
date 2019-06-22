import django_filters
from .models import ProjectCenter, BidDetails


class ProjectFilter(django_filters.rest_framework.FilterSet):
    """
    自定义过滤类
    """
    labels = django_filters.CharFilter(name='labels')
    pro_type = django_filters.CharFilter(name='pro_type')

    class Meta:
        model = ProjectCenter
        fields = ['labels', 'pro_type']

# class MyProjectFilter(django_filters.rest_framework.FilterSet):
#     """
#     我的项目中心过滤项目列表
#     """
#     Myproject = django_filters.CharFilter(name='user_id')
#
#     # MyBidProject = django_filters.CharFilter(name='labels')
#
#     class Meta:
#         model = ProjectCenter
#         fields = ['user_id']
