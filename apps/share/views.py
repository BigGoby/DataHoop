import json
import io
import xlwt
import pymongo

from rest_framework.response import Response
from rest_framework import mixins, viewsets
from rest_framework.views import APIView
from .models import SharingFile, SharingConsume
from users.models import UserProfile
from rest_framework.pagination import PageNumberPagination
from bson.objectid import ObjectId
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.authentication import SessionAuthentication
from utils.permissions import IsOwnerOrReadOnly
from django.http import HttpResponse, FileResponse, JsonResponse
from django.conf import settings
from files.models import DataSource
from algorithm.models import Algorithms, ModelResult
from .serializers import DataSourceSerializer, AlgorithmsSerializer, ModelResultSerializer
from .filter import DataSourceFilter, AlgorithmsFilter, ModelResultFilter
from personalcenter.models import Collect

mg_client = pymongo.MongoClient(settings.MONGO_DB_URI)
db = mg_client.datahoop.data


# 数据分页
class FilePagination(PageNumberPagination):
    page_size = 10
    # page_size_query_param = 'page_size'
    # page_query_param = "p"
    # max_page_size = 100


# 共享数据搜索，排序，分页，筛选
class FileViewSet(mixins.ListModelMixin,
                  viewsets.GenericViewSet,
                  mixins.RetrieveModelMixin,
                  ):
    """
    共享数据接口

    文件搜索，排序，分页，筛选
    """
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer
    pagination_class = FilePagination

    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_class = DataSourceFilter
    search_fields = ('file_name',)
    ordering_fields = ('thumb_num', 'create_time', 'views_num', 'fav_num', 'download_num')
    ordering = ('-create_time',)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views_num += 1
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# 共享算法搜索，排序，分页，筛选
class AlgViewSet(mixins.ListModelMixin,
                 viewsets.GenericViewSet,
                 mixins.RetrieveModelMixin,
                 ):
    """
    共享算法接口

    文件搜索，排序，分页，筛选
    """
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    queryset = Algorithms.objects.all()
    serializer_class = AlgorithmsSerializer
    pagination_class = FilePagination

    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_class = AlgorithmsFilter
    search_fields = ('name',)
    ordering_fields = ('thumb_num', 'add_time', 'view_num', 'fav_num', 'download_num')
    ordering = ('-add_time',)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.view_num += 1
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# 共享模型搜索，排序，分页，筛选
class ModelViewSet(mixins.ListModelMixin,
                   viewsets.GenericViewSet,
                   mixins.RetrieveModelMixin,
                   ):
    """
    共享模型接口

    模型搜索，排序，分页，筛选
    """
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    queryset = ModelResult.objects.all()
    serializer_class = ModelResultSerializer
    pagination_class = FilePagination

    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_class = ModelResultFilter
    search_fields = ('ModelName',)
    ordering_fields = ('thumb_num', 'add_time', 'views_num', 'collect_num', 'download_num')
    ordering = ('-add_time',)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.view_num += 1
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ClickView(APIView):
    '''
    点赞，收藏

    {

        type:get,

        url:/share/click/,

        data:{id:'文件的id'

              way:操作方式（赞，取消赞）

              which:当前点击的分类（'数据，算法，模型'）},

        dataType:JSON,

    }

    {

        type:post,

        url:/share/click/,

        data:{id:'文件的id'

              way:操作方式（收藏，取消收藏）

              which:当前点击的分类（'数据，算法，模型'）},

        dataType:JSON,

    }
    '''

    def get(self, request):
        id = request.GET.get('id', '')
        way = request.GET.get('way', '')
        which = request.GET.get('which', '')
        try:
            if which == '数据':
                thumb = DataSource.objects.get(id=id)
            elif which == '算法':
                thumb = Algorithms.objects.get(id=id)
            else:
                thumb = ModelResult.objects.get(id=id)
            if way == '赞':
                thumb.thumb_num += 1
                thumb.save()
            else:
                thumb.thumb_num -= 1
                thumb.save()
            return_json = {'status': True, 'data': None, 'msg': '返回成功'}
            return HttpResponse(json.dumps(return_json), content_type='application/json')

        except Exception as e:
            print(e)
            return_json = {'status': False, 'data': None, 'msg': '返回失败'}
            return HttpResponse(json.dumps(return_json), content_type='application/json')

    def post(self, request):
        id = request.POST.get('id', '')
        way = request.POST.get('way', '')
        which = request.GET.get('which', '')
        try:
            if which == '数据':
                thumb = DataSource.objects.get(id=id)
            elif which == '算法':
                thumb = Algorithms.objects.get(id=id)
            else:
                thumb = ModelResult.objects.get(id=id)
            if way == '收藏':
                thumb.fav_num += 1
                thumb.save()
                item = Collect()
                item.user = request.user.id
                item.file_id = id
                item.source = which
                item.save()
            else:
                thumb.fav_num -= 1
                thumb.save()
                Collect.objects.filter(user=request.user.id, file_id=id).delete()
            return_json = {'status': True, 'data': None, 'msg': '返回成功'}
            return HttpResponse(json.dumps(return_json), content_type='application/json')

        except Exception as e:
            print(e)
            return_json = {'status': False, 'data': None, 'msg': '返回失败'}
            return HttpResponse(json.dumps(return_json), content_type='application/json')


class AddIntegralView(APIView):
    '''
    对非标0共享文件消费
    '''

    # """
    def post(self, request):
        user_id = request.user.id
        which = int(request.POST.get('which', 1))
        sharingfile_id = request.POST.get('id', '')
        sharing_consume = SharingConsume.objects.filter(user_id=user_id, sharingfile_id=sharingfile_id, which=which)
        if sharing_consume:
            return JsonResponse({'status': False, 'msg': '用户已消费'})
        if not sharing_consume:

            if which == 1:
                sharingfile = DataSource.objects.get(id=sharingfile_id)
            elif which == 2:
                sharingfile = Algorithms.objects.get(id=sharingfile_id)
            else:
                sharingfile = ModelResult.objects.get(id=sharingfile_id)

            user_score = UserProfile.objects.get(id=user_id)

            if user_score.money + user_score.bind_money < sharingfile.price:
                return JsonResponse({'status': False, 'msg': '余额不足'})
            if user_score.money + user_score.bind_money > sharingfile.price:
                sharing_consume = SharingConsume()
                sharing_consume.user_id = user_id
                sharing_consume.sharingfile_id = sharingfile_id
                sharing_consume.which = which
                sharing_consume.out = sharingfile.price
                sharing_consume.source = 2
                sharing_consume.save()
                user_score.money -= sharingfile.price
                user_score.save()
                # userid = sharingfile.user
                sharing_consume = SharingConsume()
                sharing_consume.user_id = sharingfile.user
                sharing_consume.sharingfile_id = sharingfile_id
                sharing_consume.which = which
                sharing_consume.out = sharingfile.price
                sharing_consume.source = 1
                sharing_consume.save()
                # user_score.money -= sharingfile.price
                # user_score.save()k
                return JsonResponse({'status': True, 'msg': '消费成功'})


class downloadPyFile(APIView):
    '''
    下载py文件
    '''

    def get(self, request):
        id = request.GET.get('id', 82)
        alg_file = Algorithms.objects.get(id=id)
        obj_id = alg_file.objid
        response = FileResponse(db.find({'_id': ObjectId(obj_id)})[0]['fileData'])
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename={}.py'.format(alg_file.name.split('.')[0])
        thumb = Algorithms.objects.get(id=id)
        thumb.download_num += 1
        thumb.save()
        return response


class downloadDataFile(APIView):
    def get(self, request):
        obj_id = ''
        if request.GET.get('sharingfile_id', ''):
            sharingfile = SharingFile.objects.get(id=request.GET.get('sharingfile_id', ''))
            obj_id = sharingfile.content
        if request.GET.get('obj_id', ''):
            obj_id = request.GET.get('obj_id', '')
        # mongo = DataMongo()
        data = db.find({'_id': ObjectId(obj_id)})[0]
        file_name = data['fileName']
        file_type = file_name.split('.')[1]
        data = data['fileData']
        workbook = xlwt.Workbook(encoding='utf-8')
        if file_type in ['txt', 'csv']:
            sheet = workbook.add_sheet(file_name.split('.')[0])
            for i in range(0, len(data)):
                row = data[i]
                for j in range(0, len(row)):
                    sheet.write(i, j, row[j])
        excel = io.BytesIO()
        workbook.save(excel)
        res = excel.getvalue()
        excel.close()
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename={}.xls'.format(file_name.split('.')[0])
        response.write(res)
        thumb = SharingFile.objects.get(id=id)
        thumb.download_num += 1
        thumb.save()
        return response
