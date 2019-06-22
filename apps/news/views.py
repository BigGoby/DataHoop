import json
import datetime

from .serializers import InfoSerializer
from rest_framework import mixins
from rest_framework import viewsets
from .models import Info
from rest_framework import filters
from rest_framework.views import APIView
from users.models import UserProfile
from files.models import DataSource, UserToLabel
from django.db.models import Q
from django.http import HttpResponse
from .filter import NewsFilter
from django_filters.rest_framework import DjangoFilterBackend
from algorithm.models import Algorithms, ModelResult
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated


# 项目分页
class ProjectPagination(PageNumberPagination):
    page_size = 5


class NewViewSet(mixins.ListModelMixin, viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    '''
    新闻资讯接口

    热门资讯根据点击量进行排序获取数据
    '''
    permission_classes = (IsAuthenticated,)
    queryset = Info.objects.all()
    pagination_class = ProjectPagination
    serializer_class = InfoSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filter_class = NewsFilter
    ordering_fields = ('click_num',)


class PushView(APIView):
    """
        推送

        {

            type:get,

            url:/news/push/,

            data:'way':选择的方法（算法、数据、模型）,

            dataType:JSON,

        }
        """

    def get(self, request):
        try:
            id = request.user.id
            way = request.GET.get('way', '')
            if id:
                # label_id = UserToLabel.objects.get(user=id).label_id
                if way == '算法':
                    thumb = Algorithms.objects.filter(~Q(user_id=id) & Q(is_share=1)).order_by('?')[:4]
                    files = []
                    for item in thumb:
                        dic = {}
                        dic['id'] = item.id
                        # dic['作者'] = item.user
                        dic['name'] = str(item.name)
                        dic['cite'] = item.thumb_num
                        dic['download'] = item.download_num
                        dic['label'] = [x for x in item.label.values_list('name')]
                        files.append(dic)
                    return_json = {'status': True, 'data': files, 'msg': '返回成功'}
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                elif way == '数据':
                    thumb = DataSource.objects.filter(~Q(user_id=id) & Q(share_status=0)).order_by('?')[:4]
                    files = []
                    for item in thumb:
                        dic = {}
                        dic['id'] = item.id
                        # dic['作者'] = item.user
                        dic['name'] = str(item.file_name)
                        dic['cite'] = item.thumb_num
                        dic['download'] = item.download_num
                        if item.label_name == '':
                            dic['label'] = [item.get_parent_display()]
                        else:
                            dic['label'] = [item.get_parent_display(), item.label_name]
                        files.append(dic)
                    return_json = {'status': True, 'data': files, 'msg': '返回成功'}
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                else:
                    thumb = ModelResult.objects.filter(~Q(user_id=id) & Q(is_share=1)).order_by('?')[:4]

                    files = []
                    for item in thumb:
                        dic = {}
                        dic['id'] = item.id
                        # dic['作者'] = item.user
                        dic['name'] = str(item.ModelName)
                        dic['cite'] = item.thumb_num
                        dic['download'] = item.download_num
                        dic['label'] = [x for x in item.label.values_list('name')]
                        files.append(dic)
                    return_json = {'status': True, 'data': files, 'msg': '返回成功'}
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
            else:
                print(way)
                if way == '算法':
                    thumb = Algorithms.objects.filter(is_share=1).order_by('?')[:4]
                    files = []
                    for item in thumb:
                        dic = {}
                        dic['id'] = item.id
                        # dic['作者'] = item.user
                        dic['name'] = str(item.name)
                        dic['cite'] = item.thumb_num
                        dic['download'] = item.download_num
                        dic['label'] = [x for x in item.label.values_list('name')]
                        # dic['label'] = [item.algorithms__label__name]
                        files.append(dic)
                    return_json = {'status': True, 'data': files, 'msg': '返回成功'}
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                elif way == '数据':
                    thumb = DataSource.objects.filter(share_status=0).order_by('?')[:4]
                    files = []
                    for item in thumb:
                        dic = {}
                        dic['id'] = item.id
                        # dic['作者'] = item.user.username
                        dic['name'] = str(item.file_name)
                        dic['cite'] = item.thumb_num
                        dic['download'] = item.download_num
                        if item.label_name == '':
                            dic['label'] = [item.get_parent_display()]
                        else:
                            dic['label'] = [item.get_parent_display(), item.label_name]
                        files.append(dic)
                    return_json = {'status': True, 'data': files, 'msg': '返回成功'}
                    print(files)
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                else:
                    thumb = ModelResult.objects.filter(is_share=0).order_by('?')[:4]
                    files = []
                    for item in thumb:
                        dic = {}
                        dic['id'] = item.id
                        # dic['作者'] = item.user
                        dic['name'] = str(item.ModelName)
                        dic['cite'] = item.thumb_num
                        dic['download'] = item.download_num
                        dic['label'] = [x for x in item.label.values_list('name')]
                        files.append(dic)
                    return_json = {'status': True, 'data': files, 'msg': '返回成功'}
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

        except Exception as e:
            print(e)
            return_json = {'status': False, 'data': None, 'msg': '返回失败'}
            return HttpResponse(json.dumps(return_json), content_type='application/json')


class NumView(APIView):
    '''
    平台入住数量，分享数量，分享算法数量

    url:news/num/
    '''

    def get(self, request):
        try:
            person = UserProfile.objects.all().count()
            time = datetime.datetime.now().date()
            today_person = UserProfile.objects.filter(date_joined__contains=time).all().count()
            # from share.models import SharingFile
            share_d = DataSource.objects.filter(share_status=0).count()
            share_a = Algorithms.objects.filter(is_share=1).count()
            share_m = ModelResult.objects.filter(is_share=0).count()
            # share_alg = SharingFile.objects.filter(label=3).count()
            dic = {}
            dic['person'] = person
            dic['today_person'] = today_person
            dic['share'] = share_d + share_m
            dic['share_alg'] = share_a
            return_json = {'status': True, 'data': dic, 'msg': '获取成功'}
            return HttpResponse(json.dumps(return_json), content_type='application/json')
        except Exception as e:
            print(e)
            return_json = {'status': False, 'data': None, 'msg': '获取失败'}
            return HttpResponse(json.dumps(return_json), content_type='application/json')
