from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse
from files.models import DataSource
from algorithm.models import  ModelResult, Algorithms
from files.models import Model_Label
from django.conf import settings
import json, os, base64
import requests as rq
from bson.objectid import ObjectId
from bson.objectid import string_type
from rest_framework.permissions import IsAuthenticated
from utils.permissions import UserPermissions, IsOwnerOrReadOnly
import pymongo
from rest_framework import mixins, generics, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status

# 创建mongo连接
cli = pymongo.MongoClient(settings.MONGO_DB_URI)
# 加载日志模块
from utils.logConf import log

logger = log(__name__)

from algorithm.serializers import DataSourceSerializer, ModelResultSerializer, ModelResultSerializer2, \
    GetModelLabelSerializer

from rest_framework.pagination import PageNumberPagination


class DataListView(APIView):
    """
    **获取数据文件列表:**<br>
    >`1. 返回文件名列表`<br>
    >`2. 返回文件对应表头`<br>
    >`3. 返回文件对应objid`<br>
    >相关返回值：("id","file_name","obj_id","title")
    """
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        obj = DataSource.objects.filter(user=request.user).all().order_by("-create_time")
        ser = DataSourceSerializer(instance=obj, many=True)
        print(ser.data)
        logger.info("用户--{}--获取文件名列表".format(ser.data))

        return Response(ser.data)


class ReadData(APIView):
    """
    >**获取mongodb文件数据（top100）**
    "obj_id"="5a43589c1d41c827fa65ee04"
    :return ：获取文件数据（top100）
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        _id = request.GET.get("obj_id")
        client = cli.datahoop.data
        datas = client.find_one({"_id": ObjectId(_id)}, {"fileData": {"$slice": 100}})["fileData"]
        return Response(datas) 


from algorithm.views.distributed_views import readCodeFromMongodb


class ModelPagination(PageNumberPagination):
    """模型页分页设置"""
    page_size = 30
    page_size_query_param = 'page_size'
    page_query_param = "page"
    max_page_size = 100


class ModelViewSet(viewsets.GenericViewSet, mixins.ListModelMixin,
                   mixins.RetrieveModelMixin, mixins.DestroyModelMixin):
    """
    模型详情，工作台场景页面, 获取模型数据
    """
    queryset = ModelResult.objects.all().order_by("-add_time")
    serializer_class = ModelResultSerializer
    pagination_class = ModelPagination

    def get_queryset(self):
        pass

    def readCodeFromMongodb(self, objid):
        """获取mongodb中存的code数据"""
        mongoCli = cli.mark.models
        data = mongoCli.find_one({"_id": ObjectId(objid)})["models"]
        print('###############', data)
        cli.close()
        return data

    def delCodeToMongodb(selfm, objid):
        """删除mongodb的数据"""
        mongoCli = cli.mark.models
        rel = mongoCli.remove({"_id": ObjectId(objid)})
        cli.close()
        return rel

    def retrieve(self, request, *args, **kwargs):
        """get id =? """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        rel = serializer.data
        rel["OBJID"] = self.readCodeFromMongodb(serializer.data["OBJID"])
        print(rel)
        return Response(rel)

    # 删除模型
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()


class ModelCreateViewSet(viewsets.GenericViewSet,
                         mixins.ListModelMixin,
                         mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin):
    """
    上传模型<br>
    create:
        moduleData:模型数据<br>
        ModelName:模型名称<br>

    """
    queryset = ModelResult.objects.all()
    serializer_class = ModelResultSerializer2

    permission_classes=(IsAuthenticated,)


    def saveModelToMongodb(self, model):
        """保存算法到mongodb"""
        mongoCli = cli.mark.models
        OBJ = mongoCli.insert({"model": model})
        OBJ_ID = string_type(OBJ)
        cli.close()
        return OBJ_ID

    def create(self, request, *args, **kwargs):
        """插入一条场景 信息"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 将算法存入mongodb
        serializer.validated_data["OBJID"] = self.saveModelToMongodb(serializer.validated_data["moduleData"])
        serializer.validated_data.pop("moduleData")
        logger.debug(serializer.validated_data)
        # 插入数据库
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({'status': 0, 'data': serializer.validated_data["OBJID"]}, status=status.HTTP_201_CREATED,
                        headers=headers)

    def UpdateCodeToMongodb(selfm, objid, data):
        """删除mongodb的数据"""
        mongoCli = cli.mark.models
        rel = mongoCli.update({"_id": ObjectId(objid)}, {"$set": {"model": data}})
        cli.close()
        return rel

    def update(self, request, *args, **kwargs):
        """ 更新场景模型  """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.UpdateCodeToMongodb(serializer.validated_data["OBJID"], serializer.validated_data["moduleData"])

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        print(serializer.data)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()


class GetModelLabelViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """ 获取标签数据 """
    queryset = Model_Label.objects.all()
    serializer_class = GetModelLabelSerializer


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def modelJson(request):
    """
        获取和保存模型<br>
        MJson:模型结果<br>
        MId:模型ID<br>
        modelName:模型名称<br>
        remark:模型备注<br>
        labelList:模型列表<br>
    """

    msg = {'status': True, 'data': None}
    _phone = request.user.id
    if request.method == "GET":
        _id = request.GET.get('modelid', '')
        _modelName = request.GET.get("modelName")
        try:

            obj = ModelResult.objects.get(id=_id)
            mongoCli = cli.mark.models
            msg["mjson"] = mongoCli.find_one({"_id": ObjectId(obj.OBJID)})["models"]
        except Exception as e:
            msg["status"] = False
            msg["error"] = "获取失败"
            logger.error('获取模型失败:{0}'.format(e))
        logger.info('获取模型列表:{0}'.format(msg))
        return JsonResponse(msg)

    elif request.method == "POST":
        _mJson = request.POST.get("MJson")
        logger.info("模型长度:{}".format(len(_mJson)))
        _mid = request.POST.get("MId", "")
        _remark = request.POST.get("remark", "")
        _modelName = request.POST.get("modelName")
        _labelList = json.loads(request.POST.get("labelList", [1, 2, 3]))
        print(type(_labelList), _labelList)
        _author = request.user  # 获取用户对象
        logger.debug("模型保存请求参数：{0}--{1}--{2}".format(_modelName, _labelList, _remark))

        try:
            if not _mid:
                '''没有MID值 则 判断:更新还是新建'''
                if ModelResult.objects.filter(ModelName=_modelName).count():
                    '''没有mid 但是modelName已经存在'''
                    msg['status'] = False
                    msg['error'] = '保存失败:模型名已存在,换个名字试试吧!'
                    logger.info('模型名已存在无法保存--用户:{0} ; 模型ID:{1}, 模型名称:{2}'.format(_phone, _mid, _modelName))
                else:
                    '''创建一条模型记录'''
                    mongoCli = cli.mark.models
                    OBJ = mongoCli.insert({"models": _mJson})
                    OBJ_ID = string_type(OBJ)
                    cli.close()
                    objID, status = ModelResult.objects.get_or_create(user=_author, ModelName=_modelName, OBJID=OBJ_ID,
                                                                      remark=_remark, )
                    # 保存标签
                    for i in _labelList:
                        labelObj = Model_Label.objects.get(id=i)
                        objID.label.add(labelObj)
                    objID.save()
                    logger.info("objID:{0}--状态:{1}".format(objID, status))
                    msg['modelid'] = objID.id
                    logger.info('保存成功--用户:{0} ; 模型ID:{1}, 模型名称:{2},数据:{3}'.format(_phone, _mid, _modelName, OBJ_ID))

            else:
                '''更新模型'''
                if ModelResult.objects.filter(ModelName=_modelName).exclude(id=_mid).count():
                    '''modleName保持唯一'''
                    msg['status'] = False
                    msg['error'] = '保存失败:模型名已存在,换个名字试试吧!'
                    logger.info('模型名已存在无法保存--用户:{0} ; 模型ID:{1}, 模型名称:{2}'.format(_phone, _mid, _modelName))

                else:
                    obj = ModelResult.objects.get(id=_mid)
                    obj.label.add(id=1)
                    ModelResult.objects.filter(id=_mid).update(ModelName=_modelName)
                    mongoCli = cli.mark.models
                    mongoCli.update({'_id': ObjectId(obj.OBJID)}, {"models": _mJson})
                    cli.close()
                    msg['modelid'] = _mid
                    logger.info('更新成功--用户:{0} ; 模型ID:{1}, 模型名称:{2},数据:{3}'.format(_phone, _mid, _modelName, obj.OBJID))

        except Exception as e:
            logger.error('模型保存失败:{0}'.format(e))
            msg['status'] = False
            msg['error'] = '保存失败!'
        return JsonResponse(msg)


def MarkData(objId):
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
        logger.debug("获取成功")

    except Exception as e:
        logger.info("读取文件失败：%s" % e)
        return {"error": "读取文件失败"}
    logger.debug("返回mongodb数据.")
    return dataOld


def DataHoopData(objId):
    '''
    DataHoop 读取预处理数据集合结果
    :param objId:
    :return:
    '''
    logger.debug('读取预处理数据集合结果objId:{0}'.format(objId))
    try:
        client = cli.datahoop.data
        data = client.find_one({"_id": ObjectId(objId)}, {"fileData": {"$slice": 100}})["fileData"]
        result = client.find_one({"_id": ObjectId(objId)})["result"]
        datatitle = data[0]
        # client.close()
    except Exception as e:
        logger.info("读取文件失败：%s" % e)
        return "读取失败", "读取失败", "读取失败"
    # print(data, datatitle)
    return data, datatitle, result
    # return  render(request,"test.html",{"msg":msg})


# 调用算法
from demoCelery import tasks


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def importRpc(request):
    '''
    **除标准化和预处理的算法请求**
    >样例：
    >> 参数名称：defApp    值： “KNN_func”<br>
    >> 参数名称：cn_list   值：["5a000143b6cb5517986d6ae9","","0,1,2","9",5,"uniform",2,0.5,1]<br>

    >> return :{'status': True, 'error': None, 'data': None,'objId',None,}
    '''

    msg = {'status': True, 'error': None, 'data': None}
    if request.method == "GET":
        arg_list = request.GET.get("cn_list", ['5a96586f3d7ac4f07e0c1512', '', '1', 2, False])
        defApp = request.GET.get("defApp", 'MovingAverage_func')
        print(type(arg_list), arg_list)
        _user = request.user
        logger.info("用户：userID:{0}-- 的用户算法：{1} -- 参数 {2}".format(_user, defApp, arg_list))

        if not arg_list or not defApp:
            msg = {'status': True, 'error': None, 'data': None}
            return msg

        cn_list = json.loads(arg_list)
        logger.debug('参数值：{0} -- 类型：{1}'.format(cn_list, type(cn_list)))
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
                    msg["error"] = "执行失败！"
                    return JsonResponse(msg)

            logger.info("用户: {0} --{1}:的执行结果:（{2}）。".format(_user, defApp, rel))
            rel = json.loads(rel)
            if rel["status"] == True:
                msg["objId"] = rel["data"]
                data = MarkData(msg["objId"])
                logger.debug('-------------------------------{0}--{1}'.format(type(data), data))
                if data.get('train_confusion_matrix', False):
                    data["train_confusion_matrix"] = 'train_confusion_matrix'
                if data.get('train_confusion_matrix', False):
                    data["test_confusion_matrix"] = 'test_confusion_matrix'
                if data.get('test_decision_boundary_fig', False):
                    data["test_decision_boundary_fig"] = 'test_decision_boundary_fig'
                if data.get('train_decision_boundary_fig', False):
                    data["train_decision_boundary_fig"] = 'test_decision_boundary_fig'
                if data.get('原始数据季节分解图', False):
                    data["原始数据季节分解图"] = ''
                    data["original_data_season_decomposition"] = data.pop('原始数据季节分解图')
                if data.get('Dendrogram_data', False):
                    data["Dendrogram_data"] = 'Dendrogram_data'
                if data.get('平方距离矩阵', False):
                    data["Square_distance_matrix"] = data.pop("平方距离矩阵")  # 替换掉汉字

                msg['data'] = data
                logger.debug(msg)
                return JsonResponse(msg)
            else:
                logger.debug(rel)
                return JsonResponse(rel)
        except Exception as e:
            logger.error("执行失败：%s" % e)
            msg["status"] = False
            msg["error"] = "请检查数据!"
            # client.close()
            # msg = json.loads(msg)
            return JsonResponse(msg)



import time
from functools import wraps

def log_time_delta(func):
    #  这是为了保持原函数的元数据不被装饰过程改变
    @wraps(func)
    def deco(request):
        start = time.time()
        res = func(request)
        end = time.time()
        delta = end - start
        print("%s用户%s函数运行%f秒"%(request.user.id,func.__name__,delta))
        return res
    return deco

@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@log_time_delta
def importRpcScaler(request):
    '''
    标准化算法请求
    :param request:
    :return:
    '''
    msg = {'status': True, 'error': None, 'data': None}
    if request.method == "GET":
        arg_list = request.GET.get("cn_list")

        defApp = request.GET.get("defApp", "")
        _userId = request.user.id
        logger.info("userID:%s" % _userId)
        cn_list = json.loads(arg_list)
        logger.info("执行算法:{0}--{1}".format(defApp, cn_list))
        try:
            rel = getattr(tasks, defApp, 'no exit').delay(*cn_list)
            while True:
                if rel.ready():
                    rel = rel.result
                    logger.info(rel)
                    break
            logger.info("{0}:的执行结果:（{1}）。".format(defApp, rel))
            rel = json.loads(rel)
            if rel['status'] == True:
                logger.debug(rel)
                client = cli.datahoop.data
                data = client.find_one({"_id": ObjectId(rel["data"])}, {"fileData": {"$slice": 100}})
                print("**************",data)
                rel["objId"] = rel["data"]
                rel["data"] = data["fileData"]
                rel["result"] = data["result_data"]
                print("----------",rel)
                return Response(rel)
            else:
                msg['status'] = False
                msg["error"] = rel["error"]
                return Response(msg)
        except Exception as e:
            logger.error("执行失败：%s" % e)
            msg = dict()
            msg["status"] = False
            msg["error"] = "请检查数据和参数!"
            return Response(msg)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def importRpcPretreatment(request):
    '''
    预处理算法请求
    :param request:
    :return:
    '''
    msg = {'status': True, 'error': None, 'data': None}
    if request.method == "GET":
        arg_list = request.GET.get("cn_list")
        defApp = request.GET.get("defApp", "")
        _userId = request.user.id
        logger.info("userID:%s" % _userId)
        cn_list = json.loads(arg_list)
        logger.info("执行算法:{0}--{1}".format(defApp, cn_list))
        try:
            rel = getattr(tasks, defApp, 'no exit').delay(*cn_list)
            while True:
                if rel.ready():
                    rel = rel.result
                    logger.info(rel)
                    break
            logger.info("{0}:的执行结果:（{1}）。".format(defApp, rel))
            rel = json.loads(rel)
            if rel['status'] == True:
                msg["objId"] = rel["data"]
                msg["data"], msg["datatitle"], msg["result"] = DataHoopData(msg["objId"])
                return JsonResponse(msg)
            else:
                msg['status'] = False
                msg["error"] = rel["error"]
                return JsonResponse(msg)
        except Exception as e:
            logger.error("执行失败：%s" % e)
            msg = {}
            msg["status"] = False
            msg["error"] = "请检查数据和参数!"
            return Response(msg)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def readMarkData(request):
    '''
    从mongodb获取算法的执行结果
    :param request:
    :return:
    '''
    msg = {'status': True, 'error': None, 'data': None, 'title': None}
    if request.method == "GET":
        _id = request.GET.get("objId", '')
        try:
            client = cli.mark.algo_collection
            dataOld = client.find_one({"_id":ObjectId(_id)})["fileData"]
            sheetList = dataOld.keys()
            sheetList = list(sheetList)
            msg["title"] = sheetList
            msg["data"] = dataOld
            client.close()
            logger.info('获取成功:'.format(msg))
        except Exception as e:
            logger.info("读取文件失败：%s" % e)
            msg["status"] = False
            msg["error"] = "读取文件失败"
        return Response({"msg": msg},status=status.HTTP_200_OK)


# 提供模型搭建结果中的 : 混淆矩阵图 / 决策边界图  / 树图等图片
@api_view(['GET'])
def visualization(request):
    """
    提供模型搭建结果中的 : 混淆矩阵图 / 决策边界图  / 树图等图片<br>
    type:图片名称，objID:objid

    """
    if request.method == "GET":
        _type = request.GET.get("type", '')
        _objID = request.GET.get("objID", '')
        logger.info('{0}--{1}'.format(_type, _objID))
        # 获取type成功,请求图片,否则返回默认图片
        if _type:
            image_data = MarkData(_objID)[_type]
            logger.info('图片请求成功:{0}----{1}'.format(_type, image_data))
            return HttpResponse(image_data, content_type="image/png")
        else:
            image_data = open(os.path.join(settings.PIC_PATH, '1.jpg'), "rb").read()
            return HttpResponse(image_data, content_type="image/png")


def MongoDataToExcel(request):
    '''
    DataHoop 读取数据集合结果
    :param objId:
    :return:
    '''
    objId = request.GET.get('objID', '5a31f081ad5bfb43a82d3812')
    print('objId:', objId)
    try:
        client = cli.datahoop.data

        datatitle = client.find_one({"_id": ObjectId(objId)}, {"fileData": {"$slice": 1}})["fileData"]
        data = client.find_one({"_id": ObjectId(objId)})["fileData"]
        result = client.find_one({"_id": ObjectId(objId)})["result"]
        print(result.keys())
        print(type(result))
        print(data)


    except Exception as e:
        logger.info("读取文件失败：%s" % e)
        return "读取失败", "读取失败", "读取失败"
    # print(data, datatitle)
    # return data, datatitle, result
    return JsonResponse(result)


import xlwt
from io import BytesIO


@api_view(['GET'])
def ExportContentByJiraVersion(request, site_name="result", jira_version=None):
    """
    模型结果下载<br>
    :param request:<br>
    :param site_name:文件名<br>
    :param jira_version:版本号<br>
    :param objID:ObjectId<br>
    :return:
    """
    objID = request.GET.get("obj_id")
    # ObjectId("5a31f081ad5bfb43a82d3812")
    # ObjectId("5a337ca2ad5bfb18f8729681")
    # client = cli.datahoop.data
    # ObjectId("5a976d43b66db27c1bc87fc2")
    client = cli.mark.algo_collection
    # datatitle = client.find_one({"_id": ObjectId(objId)}, {"fileData": {"$slice": 1}})["fileData"]
    datas = client.find_one({"_id": ObjectId(objID)},{"_id":0,"fileData":1})["fileData"]
    print(datas, type(datas))
    sheets = []  # 保存所有的sheet名字
    if isinstance(datas, dict):
        sheets = datas.keys()  # 获取所有key，做为sheet名
    elif isinstance(datas, list):
        sheets = ["Data"]  # 默认sheet名:Data

    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment;filename={0}.xls'.format(site_name)
    wb = xlwt.Workbook(encoding='utf-8')
    print(sheets)
    for sheet_name in sheets:
        if isinstance(datas[sheet_name], list):
            logger.info("获取{0}中的数据".format(sheet_name))
            sheetName = wb.add_sheet(sheet_name)

            style_heading = xlwt.easyxf("""
                font:
                    name Arial,
                    colour_index white,
                    bold on,
                    height 240;
                align:
                    wrap off,
                    vert center,
                    horiz center;
                pattern:
                    pattern solid,
                    fore-colour 0x19;
                borders:
                    left THIN,
                    right THIN,
                    top THIN,
                    bottom THIN;
                """
                                        )
            style_body = xlwt.easyxf("""
                font:
                    name Arial,
                    bold off,
                    height 200;
                align:
                    wrap on,
                    vert center,
                    horiz left;
                borders:
                    left THIN,
                    right THIN,
                    top THIN,
                    bottom THIN;
                """
                                     )
            style_green = xlwt.easyxf(" pattern: pattern solid,fore-colour 0x11;")
            style_red = xlwt.easyxf(" pattern: pattern solid,fore-colour 0x0A;")
            fmts = [
                'M/D/YY',
                'D-MMM-YY',
                'D-MMM',
                'MMM-YY',
                'h:mm AM/PM',
                'h:mm:ss AM/PM',
                'h:mm',
                'h:mm:ss',
                'M/D/YY h:mm',
                'mm:ss',
                '[h]:mm:ss',
                'mm:ss.0',
            ]
            # style_body.num_format_str = fmts[0]
            # 1st line
            coul_count = (datas[sheet_name]).__len__()
            for i in range(coul_count):
                if isinstance(datas[sheet_name][i], list):
                    line_count = (datas[sheet_name][i]).__len__()
                    for j in range(line_count):
                        if i == 0:
                            sheetName.write(0, j, datas[sheet_name][i][j], style_heading)
                            sheetName.col(j).width = 100 * 50  # 第一行加宽
                        else:
                            sheetName.write(i, j, datas[sheet_name][i][j], style_body)
                elif isinstance(datas[sheet_name][i], dict):
                    pass
                elif isinstance(datas[sheet_name][i], str):
                    sheetName.write(0, i, datas[sheet_name][i], style_heading)
                    sheetName.col(i).width = 100 * 50  # 第一行加宽
                elif isinstance(datas[sheet_name][i], int) or isinstance(datas[sheet_name][i], float):
                    sheetName.write(0, i, datas[sheet_name][i], style_heading)
                    sheetName.col(i).width = 100 * 50  # 第一行加宽

    output = BytesIO()
    print("------------------")
    wb.save(output)
    output.seek(0)
    response.write(output.getvalue())
    return response


@api_view(['GET'])
def TableDataToExcel(request):
    """
    数据文件下载<br>
    :param request:
    :param site_name:文件名
    :param jira_version:版本号
    :return:
    """
    objID = request.GET.get("objID", "5a93b1fa1f812615bc3c3af4")

    client = cli.datahoop.data
    datas = client.find_one({"_id": ObjectId(objID)})["fileData"]
    obj = DataSource.objects.get(obj_id=objID)
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment;filename={0}'.format(obj.file_name)
    wb = xlwt.Workbook(encoding='utf-8')
    sheet_name = 'table'
    logger.info("获取{0}中的数据".format(sheet_name))
    sheetName = wb.add_sheet(sheet_name)
    style_heading = xlwt.easyxf("""
        font:
            name Arial,
            colour_index white,
            bold on,
            height 240;
        align:
            wrap off,
            vert center,
            horiz center;
        pattern:
            pattern solid,
            fore-colour 0x19;
        borders:
            left THIN,
            right THIN,
            top THIN,
            bottom THIN;
        """
                                )
    style_body = xlwt.easyxf("""
        font:
            name Arial,
            bold off,
            height 200;
        align:
            wrap on,
            vert center,
            horiz left;
        borders:
            left THIN,
            right THIN,
            top THIN,
            bottom THIN;
        """
                             )
    style_green = xlwt.easyxf(" pattern: pattern solid,fore-colour 0x11;")
    style_red = xlwt.easyxf(" pattern: pattern solid,fore-colour 0x0A;")
    fmts = [
        'M/D/YY',
        'D-MMM-YY',
        'D-MMM',
        'MMM-YY',
        'h:mm AM/PM',
        'h:mm:ss AM/PM',
        'h:mm',
        'h:mm:ss',
        'M/D/YY h:mm',
        'mm:ss',
        '[h]:mm:ss',
        'mm:ss.0',
    ]
    # style_body.num_format_str = fmts[0]
    # 1st line
    coul_count = datas.__len__()
    for i in range(coul_count):
        if isinstance(datas[i], list):
            line_count = (datas[i]).__len__()
            for j in range(line_count):
                if i == 0:
                    sheetName.write(0, j, datas[i][j], style_heading)
                    sheetName.col(j).width = 100 * 50  # 第一行加宽
                else:
                    sheetName.write(i, j, datas[i][j], style_body)
                    # elif isinstance(datas[sheet_name][i],dict):
                    #     pass
                    # elif isinstance(datas[sheet_name][i],str):
                    #         sheetName.write(0, i, datas[sheet_name][i], style_heading)
                    #         sheetName.col(i).width = 100 * 50  # 第一行加宽
                    # elif isinstance(datas[sheet_name][i],int) or isinstance(datas[sheet_name][i],float):
                    #         sheetName.write(0, i, datas[sheet_name][i], style_heading)
                    #         sheetName.col(i).width = 100 * 50  # 第一行加宽

    output = BytesIO()
    print("------------------")
    wb.save(output)
    output.seek(0)
    response.write(output.getvalue())
    return response


#  python在线编码程序
import os, sys, subprocess, tempfile, time
# 创建临时文件夹,返回临时文件夹路径
TempFile = tempfile.mkdtemp(suffix='_test', prefix='python_')
# 文件名
FileNum = int(time.time() * 1000)
# python编译器位置
EXEC = sys.executable
# 获取python版本
def get_version():
    v = sys.version_info
    version = "python %s.%s" % (v.major, v.minor)
    return version

# 获得py文件名
def get_pyname():
    global FileNum
    return 'test_%d' % FileNum

# 接收代码写入文件
def write_file(pyname, code):
    fpath = os.path.join(TempFile, '%s.py' % pyname)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(code)
    print('file path: %s' % fpath)
    return fpath

# 编码
def decode(s):
    try:
        return s.decode('utf-8')
    except UnicodeDecodeError:
        return s.decode('gbk')

# 主执行函数
def main(code):
    r = dict()
    r["version"] = get_version()
    pyname = get_pyname()
    fpath = write_file(pyname, code)
    try:
        # subprocess.check_output 是 父进程等待子进程完成，返回子进程向标准输出的输出结果
        # stderr是标准输出的类型
        outdata = decode(subprocess.check_output([EXEC, fpath], stderr=subprocess.STDOUT, timeout=5))
    except subprocess.CalledProcessError as e:
        # e.output是错误信息标准输出
        # 错误返回的数据
        r["code"] = 'Error'
        r["output"] = decode(e.output)
        return r
    else:
        # 成功返回的数据
        r['output'] = outdata
        r["code"] = "Success"
        return r
    finally:
        # 删除文件(其实不用删除临时文件会自动删除)
        try:
            os.remove(fpath)
        except Exception as e:
            exit(1)


#  在线编辑器运行python代码
class onlineAlgo(APIView):
    def post(self,request):
        code = request.data['code']
        jsondata = main(code)
        if jsondata['code'] != 'Success':
            return Response({'msg': jsondata['output'], 'status': False})
        # {'output': '123\r\n', 'version': 'python 3.5', 'code': 'Success'}
        return Response({'msg': jsondata['output'], 'version':jsondata['version'],
                         'status': True})


#  自定义算法执行
class CustomAlgs(APIView):
    """自定义算法执行"""
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        user = request.user
        '''提交和调用算法'''
        logger.debug("{0}-执行自定义算法请求！".format(user))
        id = request.GET.get("id")
        _objID = request.GET.get("objid", '5a3cb3c3b6cb557c5582c6a9')
        _sheet = ""
        obj = Algorithms.objects.get(id=id)
        _base64Code = readCodeFromMongodb(obj.objid)
        print(_base64Code)
        code = base64.b64decode(_base64Code).decode(encoding="utf-8")  # 解码base64数据
        print('-----------------')
        print(code)
        logger.debug("{0}执行代码：{1}".format(user, code))
        # 调用算法
        # IP地址
        _algIP = settings.ALGO_HOST
        ALG_URL = r"http://{0}/run?code={1}&objid={2}&sheet={3}".format(_algIP, _base64Code, _objID, _sheet)
        logger.debug("自定义算法请求：url:{0}".format(ALG_URL))
        rel = rq.get(ALG_URL)
        r = rel.json()
        logger.debug("自定义算法执行结果：".format(r))
        return Response(r)


