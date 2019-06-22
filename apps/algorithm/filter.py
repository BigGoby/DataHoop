import django_filters

from files.models import AlgoLabel


class algFilter(django_filters.rest_framework.FilterSet):
    label = AlgoLabel
