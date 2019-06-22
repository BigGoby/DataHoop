from django.shortcuts import HttpResponse
from django.http import JsonResponse, FileResponse
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework import status
from rest_framework import mixins
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from personalcenter.models import Collect, Love, Relationship
from algorithm.serializers import *
from django.db.models import Q
from bson.objectid import ObjectId, string_type
from files.models import AlgoLabel
from django.conf import settings
from algorithm import models
import json
from SparkCelery import tasks
from hdfs.client import Client
from hdfs.util import HdfsError
import os
import re
import base64

# 加载日志模块
from utils.logConf import log

logger = log(__name__)

# 创建mongo连接
import pymongo

cli = pymongo.MongoClient(settings.MONGO_DB_URI)


def saveCodeToMongodb(code, configuration):
    """保存算法代码到mongodb"""
    mongoCli = cli.mark.algo
    OBJ = mongoCli.insert({"code": code, "configuration": configuration})
    OBJ_ID = string_type(OBJ)
    cli.close()
    return OBJ_ID


def readCodeFromMongodb(objid):
    """获取mongodb中存的code数据"""
    mongoCli = cli.mark.algo
    data = mongoCli.find_one({"_id": ObjectId(objid)})["code"]
    cli.close()
    return data


def UpdateCodeToMongodb(objid, data):
    """更新mongodb的数据"""
    mongoCli = cli.mark.algo
    rel = mongoCli.update({"_id": ObjectId(objid)}, {"$set": {"code": data}})
    cli.close()
    return rel


def delCodeToMongodb(objid):
    """删除mongodb的数据"""
    mongoCli = cli.mark.algo
    rel = mongoCli.remove({"_id": ObjectId(objid)})
    cli.close()
    return rel


# 算法收藏
class ClickCollect(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        _id = request.GET.get("id")
        _source = request.GET.get("action")
        obj = Collect.objects.filter(user=user, file_id=_id, source=_source)
        if obj.count() == 0:
            Collect.objects.create(user=user, file_id=_id, source=_source)
            # 点赞加一
            objs = Algorithms.objects.get(id=_id)
            objs.fav_num += 1
            objs.save()
            return Response({"data": "收藏成功"}, status=status.HTTP_200_OK)
        else:
            obj.delete()
            # 点赞减一
            objs = Algorithms.objects.get(id=_id)
            objs.fav_num -= 1
            objs.save()
            return Response({"data": "取消收藏成功"}, status=status.HTTP_200_OK)


# 算法喜欢
class ClickLove(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        _id = request.GET.get("id")
        _source = request.GET.get("action")
        obj = Love.objects.filter(user=user, file_id=_id, source=_source)
        if obj.count() == 0:
            # 增加点赞记录
            Love.objects.create(user=user, file_id=_id, source=_source)
            # 点赞加一
            objs = Algorithms.objects.get(id=_id)
            objs.thumb_num += 1
            objs.save()
            return Response({"data": "喜欢成功"}, status=status.HTTP_200_OK)
        else:
            # 删除点赞记录
            obj.delete()
            # 点赞减一
            objs = Algorithms.objects.get(id=_id)
            objs.thumb_num -= 1
            objs.save()
            return Response({"data": "取消喜欢成功"}, status=status.HTTP_200_OK)


# 算法下载
class DownloadAlgo(APIView):
    # permission_classes = (IsAuthenticated,)
    def get(self, request):
        _id = request.GET.get("id")
        try:
            obj = Algorithms.objects.filter(id=_id)
            db = cli.mark.algo
            data = db.find({'_id': ObjectId(obj[0].objid)})[0]['code']
            # response = HttpResponse(content_type='py/plain')
            response = FileResponse(data)
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = 'attachment;filename={0}.py'.format(obj[0].name)
            # response.write(readCodeFromMongodb(obj.objid))
            objs = Algorithms.objects.get(id=_id)
            objs.download_num += 1
            return response
        except Exception as e:
            logger.debug(e)
            return JsonResponse({"data": "文件不存在！"})


# 添加至我的算法
class Add_Data(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        mongoCli = cli.mark.algo
        try:
            _id = request.GET.get('id')
            logger.debug("_id:{0}".format(_id))
            obj = Algorithms.objects
            obj_old = obj.get(id=_id)
            objid = obj_old.objid

            count = obj.filter(user=request.user, objid=objid).count()
            if count > 0:
                return Response({'status': True, 'msg': '添加成功'}, status=status.HTTP_200_OK)
            try:
                data = mongoCli.find_one({'_id': ObjectId(objid)}, {"code": 1, "configuration": 1})
                logger.debug(data)
                objid_new = mongoCli.insert({"code": data["code"], "configuration": data["configuration"]})
                logger.debug("新的objid{0}".format(objid_new))
                obj.create(user=request.user, name=obj_old.name, type=obj_old.type,
                           objid=objid_new)
                return Response({'status': True, 'msg': '添加成功'}, status=status.HTTP_200_OK)
            except Exception as e:
                logger.debug(e)
                return Response({'status': False, 'msg': '添加失败'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.debug(e)
            return Response({'status': False, 'msg': '添加失败'}, status=status.HTTP_400_BAD_REQUEST)


# 批量添加算法
class Add_Data_list(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        mongoCli = cli.mark.algo
        try:
            _idlist = json.loads(request.GET.get('idList'))
            print(_idlist, type(_idlist))
            logger.debug("_id:{0}".format(_idlist))
            obj = Algorithms.objects
            for _id in _idlist:
                obj_old = obj.get(id=_id)
                objid = obj_old.objid
                count = obj.filter(user=request.user, objid=objid).count()
                if count > 0:
                    continue
                try:
                    data = mongoCli.find_one({'_id': ObjectId(objid)}, {"code": 1, "configuration": 1})
                    logger.debug(data)
                    objid_new = mongoCli.insert({"code": data["code"], "configuration": data["configuration"]})
                    logger.debug("新的objid{0}".format(objid_new))
                    obj.create(user=request.user, name=obj_old.name, type=obj_old.type, objid=objid_new)
                except Exception as e:
                    logger.debug(e)
                    return Response({'status': False, 'msg': '添加失败'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'status': True, 'msg': '添加成功'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.debug(e)
            return Response({'status': False, 'msg': '添加失败'}, status=status.HTTP_400_BAD_REQUEST)


# 批量添加资源配置
class Add_Source_list(APIView):
    """
    name : 0.计算   1.存储
    size : 0.底     1.中    2.高
    sizeList : [3,2,7] 根据size的顺序填写 各个资源的购买个数
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        _sourceName = request.GET.get("name")
        _allocation = request.GET.get("size")
        _sizeList = json.dumps(request.GET.get('sizeList'))

        try:
            obj = models.ResourceAllocation.objects
            count = 0
            for i in _sizeList:
                try:
                    obj.create(user=request.user, name=_sourceName, allocation=_allocation, num=i)
                except Exception as e:
                    logger.debug(e)
                    return Response({'status': False, 'msg': '添加失败'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'status': True, 'msg': '添加成功'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.debug(e)
            return Response({'status': False, 'msg': '添加失败'}, status=status.HTTP_400_BAD_REQUEST)


# 验证是否为base64编码数据
def is_base64_code(s):
    '''Check s is Base64.b64encode'''
    if not isinstance(s, str) or not s:
        raise (ValueError, "params s not string or None")

    _base64_code = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I',
                    'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R',
                    'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a',
                    'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
                    'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's',
                    't', 'u', 'v', 'w', 'x', 'y', 'z', '0', '1',
                    '2', '3', '4', '5', '6', '7', '8', '9', '+',
                    '/', '=']

    # Check base64 OR codeCheck % 4
    code_fail = [i for i in s if i not in _base64_code]
    if code_fail or len(s) % 4 != 0:
        return False
    return True


class AlgorithmPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    page_query_param = "page"
    max_page_size = 100


# 刷新首页出现的算法
class AlgoViewSet(viewsets.GenericViewSet,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin):
    """
    返回算法列表，算法详情
    list:
        GET 请求：首页算法展示、搜索<br>
        id:算法id<br>
        name：算法名称<br>
        user：所有者<br>
        argument:算法参数<br>
        isNew:是否最新<br>
        label:标签<br>
        is_share:是否共享 0否 1是<br>
        share_num:分享次数<br>
        view_num:浏览次数<br>
        download_num:下载次数<br>
        fav_num:收藏次数<br>
        type:类型 （单机|分布）<br>
        status：状态（0启用|1启用）<br>
        price：价钱<br>
        add_time:创建时间<br>
        trial：是否试算(0是|1否)<br>

    read:
        id：算法id
        获取单个算法
    """
    queryset = Algorithms.objects.filter(is_share=1).all()
    serializer_class = AlgGetSerializer
    # 筛选和查找功能
    filter_backends = (filters.SearchFilter, DjangoFilterBackend,)
    search_fields = ('name', 'label__name')
    filter_fields = ('label__name',)

    def readCodeFromMongodb(self, objid):
        """获取mongodb中存的code数据"""
        mongoCli = cli.mark.algo
        data = mongoCli.find_one({"_id": ObjectId(objid)})
        code = data["code"]
        configuration = data["configuration"]
        cli.close()

        return code, configuration

    def retrieve(self, request, *args, **kwargs):
        """get id =? """
        user = request.user
        print(user)
        print(self)

        instance = self.get_object()
        serializer = self.get_serializer(instance)
        rel = serializer.data
        # 获取mongodb数据
        rel["objid"], rel["configuration"] = self.readCodeFromMongodb(serializer.data["objid"])
        # 判断编码是否为base64格式（用户 自定义编写的为 base64格式）
        if is_base64_code(rel["objid"]):
            rel["objid"] = base64.b64decode(rel["objid"]).decode(encoding='utf-8')
        # 数据访问增加浏览次数
        models.Algorithms.objects.filter(id=rel["id"]).update(view_num=rel["view_num"] + 1)
        # 验证用户是否收藏该条记录
        count = Collect.objects.filter(source=2, user=user, file_id=rel["id"]).count()
        if count == 0:
            rel["isCollect"] = 0
        # 验证是否已经喜欢
        count = Love.objects.filter(source=2, user=user, file_id=rel["id"]).count()
        if count == 0:
            rel["isLove"] = 0
        if rel["user"]["id"] == request.user.id:
            rel["isMe"] = 1

        relation = Relationship.objects.filter(author=user)
        all = []
        for i in relation:
            all.append(i.User_ByID)
        if str(rel["user"]["id"]) in all:
            rel['is_focus'] = 1
        else:
            rel['is_focus'] = 0
        logger.debug("获取算法{0}详情:{1}".format(rel["id"], rel))
        return Response(rel)

    def list(self, request, *args, **kwargs):

        queryset = self.filter_queryset(self.get_queryset())
        for i in queryset:
            pass
        print(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer)


# 点击标签复选算法列表
class IndexAlg(APIView):
    def get(self, request):
        #   ['预处理', '分类', '回归',......] __contains
        label = json.loads(request.GET.get('label_name'))
        algoLable_id_list = []
        page = json.loads(request.GET.get('page'))
        page = int(page)
        #  从AlgoLabel表中找符合标签的在去algorithms表中共享的返回
        # [<QuerySet [<Algorithms: 2018年4月18日12:03:46>]>, <QuerySet [<Algorithms: 2>]>,......]
        if len(label) == 0 or len(label) == 9:
            # label = ['预处理', '分类', '回归','聚类','时间序列','关联分析','统计分析','网络分析','其他']
            # for i in label:
            #     algo_id = AlgoLabel.objects.filter(Q(name=i)|Q(second_name =i)).all()
            #     for l in algo_id:
            thumb = Algorithms.objects.filter(is_share=1).all()
            for item in thumb:
                algoLable_id_list.insert(0,item)
                # algoLable_id_list.append(item)
        else:
            for i in label:
                algo_id = AlgoLabel.objects.filter(Q(name=i) | Q(second_name=i)).all()
                for l in algo_id:
                    for item in l.algorithms_set.filter(is_share=1).all():
                        algoLable_id_list.insert(0,item)
        files = []
        # algoLable_id_list = list(set(algoLable_id_list))
        #   algoLable_id_list:[<QuerySet [<Algorithms: 2018年4月18日12:03:46>]>, <QuerySet [<Algorithms: 3>]>, <QuerySet [<Algorithms: 2>]>]
        # print(algoLable_id_list)
        try:
            algo_list = algoLable_id_list[page * 20 - 20:page * 20]
        except:
            algo_list = algoLable_id_list
        for item in algo_list:
            dic = {}
            try:
                dic['id'] = item.id
                dic['name'] = str(item.name)
                dic['abstract'] = item.abstract
                dic['price'] = item.price
                dic['fav_num'] = item.fav_num
                dic['download_num'] = item.download_num
                dic['thumb_num'] = item.thumb_num
                # dic['isNew'] = item.isNew
                dic['is_share'] = item.is_share
                dic['status'] = item.status
                dic['title'] = item.title
                dic['type'] = item.type
                dic['view_num'] = item.view_num
                dic['label'] = [x for x in item.label.values_list('name')]
                # my_name = []
                second_name = [x for x in item.label.values_list('second_name')]
                if len(second_name) == 0:
                    dic['label2'] = []
                else:
                    for i in second_name:
                        # my_name.append((list(i)[0]).split(','))
                        dic['label2'] = (list(i)[0]).split(',')
            except:
                continue
            files.append(dic)
        sum = len(algoLable_id_list)
        return_json = {'status': True, 'data': files, 'msg': '返回成功', 'sum': sum}
        return HttpResponse(json.dumps(return_json), content_type='application/json')


class AlgoFileViewSet(viewsets.ModelViewSet):
    """
    POST请求：算法文件上传
    """
    queryset = Algorithms.objects.all()
    serializer_class = AlgFileSerializer
    filter_backends = (filters.SearchFilter,)

    def saveCodeToMongodb(self, code, configuration):
        """保存算法代码到mongodb"""
        mongoCli = cli.mark.algo
        OBJ = mongoCli.insert({"code": code, "configuration": configuration})
        OBJ_ID = string_type(OBJ)
        cli.close()
        return OBJ_ID

    def create(self, request, *args, **kwargs):
        """插入一条算法 信息"""
        datas = request.data
        # 获取文件对象
        filedata = datas["objid"]
        filedata2 = datas["configuration"]
        # print(type(filedata2))
        # 数据读入内存（由于算法文件都比较小，所以直接读入内存）
        # print("#############",type(filedata),filedata.size)
        code = filedata.read()
        code = code.decode("utf-8")
        configuration = filedata2.read()
        try:
            configuration = json.loads(configuration.decode("utf-8"))
        except Exception as e:
            # json文件序列化不成功，返回报错信息，需要用户检查json文件正确性
            # print(type(e), )
            return Response({'status': 1, 'data': e.__str__()}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 将算法存入mongodb
        serializer.validated_data["objid"] = self.saveCodeToMongodb(code, configuration)
        serializer.validated_data["user"] = request.user
        serializer.validated_data.pop("configuration")
        serializer.validated_data.pop("isNew")
        # 插入数据库
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({'status': 0, 'data': serializer.validated_data["objid"]}, status=status.HTTP_201_CREATED,
                        headers=headers)


        # def perform_create(self, serializer):
        #     return serializer.save()


class AlgoWriteCodeSet(viewsets.GenericViewSet,
                       mixins.RetrieveModelMixin,
                       mixins.ListModelMixin,
                       mixins.DestroyModelMixin,
                       mixins.CreateModelMixin,
                       mixins.UpdateModelMixin):
    """创建、更新、删除算法"""
    queryset = Algorithms.objects.all()
    serializer_class = AlgSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('id', 'name')

    def saveCodeToMongodb(self, code, configuration):
        """保存算法代码到mongodb"""
        mongoCli = cli.mark.algo
        OBJ = mongoCli.insert({"code": code, "configuration": configuration})
        OBJ_ID = string_type(OBJ)
        cli.close()
        return OBJ_ID

    def readCodeFromMongodb(self, objid):
        """获取mongodb中存的code数据"""
        mongoCli = cli.mark.algo
        data = mongoCli.find_one({"_id": ObjectId(objid)})["code"]
        cli.close()
        return data

    def delCodeToMongodb(self, objid):
        """删除mongodb的数据"""
        mongoCli = cli.mark.algo
        rel = mongoCli.remove({"_id": ObjectId(objid)})
        cli.close()
        return rel

    def UpdateCodeToMongodb(self, objid, data):
        """更新mongodb的数据"""
        mongoCli = cli.mark.algo
        rel = mongoCli.update({"_id": ObjectId(objid)}, {"$set": {"code": data}})
        cli.close()
        return rel

    def retrieve(self, request, *args, **kwargs):
        """get id =? """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        rel = serializer.data
        rel["objid"] = self.readCodeFromMongodb(serializer.data["objid"])
        # print(rel)
        return Response(rel)

    def create(self, request, *args, **kwargs):
        """插入一条算法 信息"""
        datas = request.data
        # 获取文件对象
        filedata2 = datas["configuration"]
        # 数据读入内存（由于算法文件都比较小，所以直接读入内存）
        # print("#############",type(filedata),filedata.size)
        configuration = filedata2.read()
        configuration = configuration.decode("utf-8")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 将算法存入mongodb
        serializer.validated_data["objid"] = self.saveCodeToMongodb(serializer.validated_data["objid"], configuration)
        # serializer = self.get_serializer(data=request.data)
        serializer.validated_data.pop("configuration")

        # 插入数据库
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({'status': 0, 'data': serializer.validated_data["objid"]}, status=status.HTTP_201_CREATED,
                        headers=headers)

    def perform_create(self, serializer):
        return serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # 删除mongodb中的数据
        self.delCodeToMongodb(objid=instance.objid)
        # 删除数据库记录
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        # print(serializer.validated_data["objid"])
        self.UpdateCodeToMongodb(serializer.validated_data["objid"], serializer.validated_data["data"])

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class AlgoWriteViewSet(viewsets.GenericViewSet,
                       mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       mixins.DestroyModelMixin,
                       mixins.CreateModelMixin):
    """算法 编写+参数编写  上传"""
    queryset = Algorithms.objects.all()
    serializer_class = AlgWriteSerializer
    permission_classes = (IsAuthenticated,)

    def readCodeFromMongodb(self, objid):
        """获取mongodb中存的code数据"""
        mongoCli = cli.mark.algo
        data = mongoCli.find_one({"_id": ObjectId(objid)})["code"]
        cli.close()
        return data

    def retrieve(self, request, *args, **kwargs):
        """get id =? """
        instance = self.get_object()

        serializer = self.get_serializer(instance)
        rel = serializer.data
        # 获取
        rel["objid"], rel["configuration"] = self.readCodeFromMongodb(serializer.data["objid"])
        # 数据访问增加浏览次数
        models.Algorithms.objects.filter(id=rel["id"]).update(view_num=rel["view_num"] + 1)
        # print(self.request.user, rel["id"])
        return Response(rel)

    def saveCodeToMongodb(self, code, configuration):
        """保存算法代码到mongodb"""
        mongoCli = cli.mark.algo
        OBJ = mongoCli.insert({"code": code, "configuration": configuration})
        OBJ_ID = string_type(OBJ)
        cli.close()
        return OBJ_ID

    def create(self, request, *args, **kwargs):
        """插入一条算法 信息"""
        print(request.data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 将算法存入mongodb
        serializer.validated_data["objid"] = self.saveCodeToMongodb(serializer.validated_data["objid"],
                                                                    serializer.validated_data["configuration"])
        serializer.validated_data["user"] = request.user
        serializer.validated_data.pop("configuration")
        # 插入数据库
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({'status': 0, 'data': serializer.validated_data["objid"]}, status=status.HTTP_201_CREATED,
                        headers=headers)

    def UpdateCodeToMongodb(self, objid, data):
        """更新mongodb的数据"""
        mongoCli = cli.mark.algo
        rel = mongoCli.update({"_id": ObjectId(objid)}, {"$set": {"code": data}})
        cli.close()
        return rel

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        # print(serializer.validated_data["objid"])
        self.UpdateCodeToMongodb(serializer.validated_data["objid"], serializer.validated_data["configuration"])
        self.perform_update(serializer)
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        return Response(serializer.data)


class GetAlgoLabelViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """ 获取算法标签数据 """
    queryset = AlgoLabel.objects.all()
    serializer_class = GetAlgoLabelSerializer


class SavePyfileViewSet(APIView):
    """ 自定义算法文件上传保存<br>
    create:
        "objid": "算法内容",<br>
        "configuration": "算法配置，当前为空",<br>
        "name": "算法名称，用于展示",<br>
        "type": 算法类型（1.单机,2.分布式，3.自定义，）,<br>
        "title": "标题",<br>
        "abstract": "简介",<br>
        "user": 用户,<br>
        "label": [1,2,3] "标签列表"<br>
    """

    def post(self, request):
        datas = request.data
        filedata = datas["objid"]  # 自定义代码
        filedata2 = datas["configuration"]  # 代码json参数说明
        code = filedata.read()
        code = code.decode("utf-8")
        configuration = filedata2.read()
        try:
            configuration = json.loads(configuration.decode("utf-8"))
        except Exception as e:
            # json文件序列化不成功，返回报错信息，需要用户检查json文件正确性
            # print(type(e), )
            return Response({'status': 1, 'data': e.__str__()}, status=status.HTTP_400_BAD_REQUEST)
        # 将算法存入mongodb
        name = request.POST.get("name")  # 算法名称
        type = request.POST.get("type", 3)  # 算法类型,0.单机，1.分布式，3.自定义
        title = request.POST.get("title")  # 标题
        abstract = request.POST.get("abstract")  # 简介
        user = request.user  # 用对象
        label = json.loads(request.POST.get("label"))  # 标签列表
        logger.debug(
            "{0}:保存自定义算法--objid={1}，configuration={2}，name={3}，type={4}，title={5}，abstract={6}，label={7}".format(
                user, code, configuration, name, type, title, abstract, label
            ))
        # print(label,type(label))

        try:
            objid = saveCodeToMongodb(code, configuration)
            _objID, _status = Algorithms.objects.get_or_create(user=user, name=name, objid=objid, type=type,
                                                               title=title, abstract=abstract)
            for l in label:
                labelObj = AlgoLabel.objects.get(id=l)
                _objID.label.add(labelObj)
            _objID.save()
            logger.debug("{0}:自定义算法保存成功!".format(user))
            return Response({"status": 0, "data": "保存成功！", "id": _objID.id, "name": name}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("{0}:保存失败：{1}".format(user, e))
            return Response({"status": 1, "data": e}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        user = request.user
        id = request.GET.get("id", False)  # 算法ID
        # 如果为False，则返回所有算法的id列表
        if not id:
            obj = Algorithms.objects.filter(Q(user=user) | Q(is_share=1), Q(status=1)).values_list("id", "name")
            logger.debug(obj)
            data = [x for x in obj]
            logger.debug(data)
            return Response({"data": data}, status=status.HTTP_200_OK)
        else:

            obj = Algorithms.objects.get(id=id)
            objid = obj.objid
            code = readCodeFromMongodb(objid)
            logger.debug(code)
            return Response({"id": id, "code": code}, status=status.HTTP_200_OK)

    def put(self, request):
        id = request.data.get("id")
        code = request.data.get("objid")  # 算法代码
        obj = Algorithms.objects.get(id=id)
        rel = UpdateCodeToMongodb(obj.objid, code)
        logger.debug("{0}:更新成功！objid:{1}".format(id, rel))
        return Response({"id": id, "code": code, "data": "更新成功！"}, status=status.HTTP_200_OK)

    def delete(self, request):
        id = request.data.get("id")
        obj = Algorithms.objects.get(id=id)
        delCodeToMongodb(obj.objid)
        logger.debug("删除成功！")
        return Response({"data": "删除成功！"}, status=status.HTTP_200_OK)


class SaveCustomViewSet(APIView):
    """ 在线编写自定义算法保存<br>
    create:
        "objid": "算法内容",<br>
        "configuration": "算法配置，当前为空",<br>
        "name": "算法名称，用于展示",<br>
        "type": 算法类型（1.单机,2.分布式，3.自定义，）,<br>
        "title": "标题",<br>
        "abstract": "简介",<br>
        "user": 用户,<br>
        "label": [1,2,3] "标签列表"<br>
    """

    def post(self, request):
        objid = request.POST.get("objid")  # 自定义代码
        configuration = request.POST.get("configuration", "00000")  # 代码json参数说明
        name = request.POST.get("name")  # 算法名称
        type = request.POST.get("type", 3)  # 算法类型,0.单机，1.分布式，3.自定义
        title = request.POST.get("title")  # 标题
        abstract = request.POST.get("abstract")  # 简介
        user = request.user  # 用对象
        label = json.loads(request.POST.get("label"))  # 标签列表
        logger.debug(
            "{0}:保存自定义算法--objid={1}，configuration={2}，name={3}，type={4}，title={5}，abstract={6}，label={7}".format(
                user, objid, configuration, name, type, title, abstract, label
            ))
        # print(label,type(label))

        try:
            objid = saveCodeToMongodb(objid, configuration)
            _objID, _status = Algorithms.objects.get_or_create(user=user, name=name, objid=objid, type=type,
                                                               title=title, abstract=abstract)
            # label = json.loads(label)
            for l in label:
                labelObj = AlgoLabel.objects.get(id=l)
                _objID.label.add(labelObj)
            _objID.save()
            logger.debug("{0}:自定义算法保存成功!".format(user))
            return Response({"status": 0, "data": "保存成功！", "id": _objID.id, "name": name}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("{0}:保存失败：{1}".format(user, e))
            return Response({"status": 1, "data": e}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        user = request.user
        id = request.GET.get("id", False)  # 算法ID
        # 如果为False，则返回所有算法的id列表
        if not id:
            obj = Algorithms.objects.filter(Q(user=user) | Q(is_share=1), Q(status=1)).values_list("id", "name")
            logger.debug(obj)
            data = [x for x in obj]
            logger.debug(data)
            return Response({"data": data}, status=status.HTTP_200_OK)
        else:

            obj = Algorithms.objects.get(id=id)
            objid = obj.objid
            code = readCodeFromMongodb(objid)
            logger.debug(code)
            return Response({"id": id, "code": code}, status=status.HTTP_200_OK)

    def put(self, request):
        id = request.data.get("id")
        code = request.data.get("objid")  # 算法代码
        obj = Algorithms.objects.get(id=id)
        rel = UpdateCodeToMongodb(obj.objid, code)
        logger.debug("{0}:更新成功！objid:{1}".format(id, rel))
        return Response({"id": id, "code": code, "data": "更新成功！"}, status=status.HTTP_200_OK)

    def delete(self, request):
        id = request.data.get("id")
        obj = Algorithms.objects.get(id=id)
        delCodeToMongodb(obj.objid)
        logger.debug("删除成功！")
        return Response({"data": "删除成功！"}, status=status.HTTP_200_OK)


class AlgoModelGetViewSet(viewsets.GenericViewSet,
                          mixins.ListModelMixin,
                          mixins.RetrieveModelMixin):
    """spark 算法"""
    serializer_class = AlgModelGetSerializer

    def get_queryset(self):
        obj = Algorithms.objects.all()
        return obj

    def readCodeFromMongodb(self, objid):
        """获取mongodb中存的code数据"""
        mongoCli = cli.mark.algo
        data = mongoCli.find_one({"_id": ObjectId(objid)})
        code = data["code"]
        configuration = data["configuration"]
        logger.debug(configuration)
        cli.close()
        return code, configuration

    def retrieve(self, request, *args, **kwargs):
        """get id =? """
        instance = self.get_object()

        # print(type(instance))
        serializer = self.get_serializer(instance)
        rel = serializer.data
        # 获取
        rel["objid"], rel["configuration"] = self.readCodeFromMongodb(serializer.data["objid"])
        # 处理JSON数据
        csin_count = rel["configuration"]["csin"]
        l = sorted(csin_count.keys())
        csin_new = []
        for i in l:
            csin_new.append(csin_count[i])
        rel["configuration"]["csin"] = csin_new
        # 数据访问增加浏览次数
        # print(self.request.user, rel["id"])
        return Response(rel)


class ReadHdfsData(APIView):
    """
    >**获取HDFS文件数据（top100）**<br>
    "hdfsName","46eccfa2-1c56-11e8-a752-1008b1983d21"<br>
    :return ：获取文件数据（top100）<br>
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        _hdfsName = request.GET.get("hdfsName", "46eccfa2-1c56-11e8-a752-1008b1983d21")
        _hdfsPath = os.path.join("/datahoop/", _hdfsName)
        # print(_hdfsPath)
        try:
            # 链接HDFS,读取文件
            cli = Client(settings.HDFS_HOST)
            try:
                with cli.read(_hdfsPath, length=2000, encoding="gbk") as f:
                    datas = f.read()
            except UnicodeDecodeError:
                with cli.read(_hdfsPath, length=2000, encoding="utf8") as f:
                    datas = f.read()

            # 字符转list
            re.sub("\r\n", "\n", datas)
            datas = datas.strip('"').split('\n')
            content = []
            for i in datas:
                content.append(i.strip('"').split(","))

        except HdfsError:
            return Response(data={"error": "文件未找到或文件编码格式不符合"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data={"data": content}, status=status.HTTP_200_OK)


class ReadHdfsData2(APIView):
    """
    >**获取HDFS文件数据（top100）**<br>
    "hdfsName","46eccfa2-1c56-11e8-a752-1008b1983d21"<br>
    :return ：获取文件数据（top100）<br>
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        _hdfsName = request.GET.get("hdfsName", "46eccfa2-1c56-11e8-a752-1008b1983d21")
        _hdfsPath = os.path.join("/datahoop/", _hdfsName)
        # print(_hdfsPath)

        try:
            # 链接HDFS,读取文件
            cli = Client(settings.HDFS_HOST)
            fileName = cli.list(_hdfsPath)[1]
            # print("filename:", fileName)
            _hdfsPath = os.path.join(_hdfsPath + "/", fileName)
            # print(_hdfsPath)
            try:
                with cli.read(_hdfsPath, length=2000, encoding="gbk") as f:
                    datas = f.read()
            except UnicodeDecodeError:
                with cli.read(_hdfsPath, length=2000, encoding="utf8") as f:
                    datas = f.read()
            # 字符转list
            re.sub("\r\n", "\n", datas)
            logger.debug(datas)
            datas = datas.strip('"').split('\n')
            content = []
            for i in datas:
                content.append(i.strip('"').split(","))
        except HdfsError:
            return Response(data={"error": "文件未找到或文件编码格式不符合"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data={"data": content}, status=status.HTTP_200_OK)


def MarkData(objId):
    '''
    读取计算结果
    :param objId:
    :return:
    '''
    logger.info('读取mongodb的objId:{}'.format(objId))
    try:
        client = cli.mark.algo_collection
        dataOld = client.find_one({"_id": ObjectId(objId)})["fileData"]
        logger.debug("获取成功")

    except Exception as e:
        logger.info("读取文件失败：%s" % e)
        return {"error": "读取文件失败"}
    logger.debug("返回mongodb数据.")
    return dataOld


def ReadMarkData(objId):
    '''
    读取计算结果
    :param objId:
    :return:
    '''
    logger.info('读取mongodb的objId:{}'.format(objId))
    # objId = '5a1647fdad5bfb4c6079e920'
    try:
        client = cli.mark.algo_collection
        dataOld = client.find_one({"_id": ObjectId(objId)})["fileData"]
        # data = dataOld["Test_Model_Result"]
        # data = re.sub('(\(\))|(DenseVector),', '', data)
        # dataOld["Test_Model_Result"] = data.strip('"').strip("[").strip("]").split(",")
        logger.debug("获取成功")

    except Exception as e:
        logger.info("读取文件失败：%s" % e)
        return {"error": "读取文件失败"}
    logger.debug("返回mongodb数据.")
    print(dataOld)
    return dataOld


class SparkAlgoRpc(APIView):
    """

        **分布式算法请求**
    >样例：
    >> 参数名称：defApp    值： “KNN_func”<br>
    >> 参数名称：cn_list   值：["5a000143b6cb5517986d6ae9","","0,1,2","9",5,"uniform",2,0.5,1]<br>

    >> return :{'status': True, 'error': None, 'data': None,'objId',None,}

    """

    def get(self, request):
        msg = {'status': True, 'error': None, 'data': None}
        arg_list = request.GET.get("cn_list")
        defApp = request.GET.get("defApp")
        _user = request.user
        logger.info("用户：userID:{0}-- 的用户算法：{1} -- 参数 {2}".format(_user, defApp, arg_list))
        null = None
        if not arg_list or not defApp:
            msg = {'status': False, 'error': None, 'data': ""}
            return msg
        cn_list = json.loads(arg_list)
        logger.info('参数值：{0} -- 类型：{1}'.format(cn_list, type(cn_list)))

        logger.info("执行算法:{0}--{1}".format(defApp, cn_list))
        try:
            rel = getattr(tasks, defApp, 'no exit').delay(*cn_list)
            while True:
                if rel.status == "SUCCESS":
                    rel = rel.result
                    logger.info(rel)
                    break
                if rel.status == "FAILURE":
                    msg["status"] = False
                    msg["error"] = "执行失败,请检查数据格式和参数是否正确！"
                    return Response({"data": msg}, status=status.HTTP_200_OK)

            logger.info("用户: {0} --{1}:的执行结果:（{2}）。".format(_user, defApp, rel))
            rel = json.loads(rel)
            if rel["status"] == True:
                try:
                    rel["rel_data"] = ReadMarkData(rel["data"]["OBJ_ID"])
                except Exception as e:
                    pass
                # 算法调用成功，处理执行结果
                logger.info("用户: {0} --{1}:的执行成功:（{2}）。".format(_user, defApp, rel))
                print(rel)
                return Response({"data": rel}, status=status.HTTP_200_OK)
            else:
                msg["status"] = False
                msg["error"] = rel["error"]
                logger.debug("执行失败：用户: {0} -- {1} -- {2}）。".format(_user, defApp, rel))
                return Response({"data": msg}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("执行失败：%s" % e)
            msg["status"] = False
            msg["error"] = "请检查数据!"
            return Response({"data": msg}, status=status.HTTP_200_OK)


class HdfsDataDownload(APIView):
    """
    list:
        0.hdfsPath
        1.获取文件命<br>
        2.返回一个文件名<br>
        3.域名+/media/hdfsFile/文件名下载文件<br>
    """

    def get(self, request):
        """
         计算结果下载hdfs 文件
        :param request:
        :return:
        """
        hdfsPath = request.GET.get("hdfsPath")
        logger.debug("请求文件：{0}".format(hdfsPath))
        localPath = os.path.join(settings.BASE_DIR, 'media', 'hdfsFile')
        logger.debug("本地存储路径：{0}".format(localPath))
        # 链接HDFS下载文件
        cli = Client(settings.HDFS_HOST)
        logger.debug("HDFS连接{0}".format(cli))
        try:
            fileName = cli.list(hdfsPath)[1]
            # print("filename:", fileName)
            path = os.path.join(hdfsPath, fileName)
            logger.debug(path, localPath)
            cli.download(hdfs_path=path, local_path=localPath, overwrite=True)
        except HdfsError:
            return Response(data={"error": "文件未找到"}, status=status.HTTP_404_NOT_FOUND)

        return Response(data={"fileName": fileName}, status=status.HTTP_200_OK)


class ReadHdfsData3(APIView):
    """
    >**下载HDFS datahoop目录下的文件）**<br>
    "hdfsName","46eccfa2-1c56-11e8-a752-1008b1983d21"<br>
    :return ：获取文件数据（top100）<br>
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        _hdfsName = request.GET.get("hdfsName", "46eccfa2-1c56-11e8-a752-1008b1983d21")
        _hdfsPath = os.path.join("/datahoop/", _hdfsName)
        obj = DataSource.objects.get(format_filename=_hdfsName)
        # print(_hdfsPath)
        try:
            # 链接HDFS,读取文件
            cli = Client(settings.HDFS_HOST)
            try:
                with cli.read(_hdfsPath, encoding="gbk") as f:
                    datas = f.read()
            except UnicodeDecodeError:
                with cli.read(_hdfsPath, encoding="utf8") as f:
                    datas = f.read()
        except HdfsError:
            return Response(data={"error": "文件未找到或文件编码格式不符合"}, status=status.HTTP_400_BAD_REQUEST)

        response = HttpResponse(content_type='csv/plain')
        response['Content-Disposition'] = 'attachment; filename={0}'.format(obj.file_name)
        response.write(datas)

        return response
