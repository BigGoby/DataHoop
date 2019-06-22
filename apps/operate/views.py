from django.shortcuts import render
from rest_framework import viewsets, mixins

from .models import Community
from .serializers import CommunitySerializer

# Create your views here.


class CommunityViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    list:
        社群微信二维码列表
    """
    queryset = Community.objects.all()
    serializer_class = CommunitySerializer