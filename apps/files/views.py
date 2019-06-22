import chardet
import json
import uuid
import os
import pymongo
import pymysql
import psycopg2
import datetime
import re
import time
import pyspark.sql.types as typ

from .serializers import DatasourceSerializer
from .serializers import ExcelDatasourceSerializer
from apps.files import tools
from .models import DataSource
from .models import WeCourse
from users.models import UserLevel
from .serializers import WeCourseSerializer
from personalcenter.models import Relationship, Love
from personalcenter.models import Collect
from rest_framework.permissions import IsAuthenticated
from bson import ObjectId
from django.http import FileResponse
from bson.objectid import string_type
from Datahoop import settings
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from Datahoop.settings import LIMIT_FILE_SIZE, HDFS_HOST
from Datahoop.settings import MONGO_DB_URI
from django.http import HttpResponse, JsonResponse
from hdfs import Client


class Judge(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        obj = DataSource.objects
        author_id = request.user.id
        file_name = request.POST.get('name')
        result = obj.filter(user=author_id, file_name=file_name)
        name_list = file_name.rsplit('.', 1)[0]
        for i in name_list:
            #  除下划线和.以外的特殊字符全部返回文件名有误
            if 57 < ord(i) < 65 or 90 < ord(i) < 95 or 123 < ord(i) < 127 or ord(i) < 46 or ord(i) == 47 or ord(
                    i) == 96 or ord(i) == 12289 or ord(i) == 65306:
                return JsonResponse({'msg': '文件名特殊字符只允许(_和.)请修改后在再重新上传', 'status': False})
        if name_list == '':
            return JsonResponse({'msg': '文件名不能为空', 'status': False})
        if result:
            # message = {'msg': True, 'status': True}
            return JsonResponse({'msg': '文件已存在！请更改文件名后重新上传', 'status': False})
        else:
            return JsonResponse({'msg': '文件名符合要求', 'status': True})


class FileView(APIView):
    """
    files upload
    """
    parser_classes = (MultiPartParser, FormParser)

    #  上传文件
    def post(self, request, *args, **kwargs):
        import uuid
        permission_classes = (IsAuthenticated,)
        start_time = time.time()
        file_serializer = DatasourceSerializer(data=request.data)

        if file_serializer.is_valid():
            path = file_serializer.validated_data['file_name']
            user = request.user.id
            # 上传文件的大小
            filesize = round((path.size) / 1024 / 1024, 2)

            #  获取该用户所有文件的大小
            mydata_id = DataSource.objects.filter(user_id=user)
            myData_size = 0
            for i in mydata_id:
                try:
                    x = i.fileSize.replace("KB", '')
                    myData_size += float(x)
                except:
                    continue
            myData_size = round(myData_size / 1024, 2)  # 单位MB

            #  该用户即将上传文件加本身有的大小
            now_userDataSize = filesize + myData_size

            #  查找用户所限制文件上传容量的大小
            user_dataSize_old = UserLevel.objects.get(user_id=user).up_load

            print(type(user_dataSize_old))
            if now_userDataSize > user_dataSize_old:
                return Response({'msg': '您的数据容量不足,请清理数据后在尝试', 'status': False})
            # if 1 > 2:
            #     pass
            else:
                try:
                    is_header = file_serializer.validated_data['is_header']
                    # user =1
                    separator = file_serializer.validated_data['column_delimiter']
                except:
                    # 数据库文件没有表头,所以设置
                    is_header = ''
                    separator = '\n'
                last = (str(path).lower()).split('.')[-1].upper()
                if last == 'CSV' or last == 'TXT' or last == 'SQL':
                    if path.size > LIMIT_FILE_SIZE:
                        format_name = uuid.uuid1()
                        file_serializer.validated_data['format_filename'] = format_name
                        file_serializer.save()
                        client = Client(HDFS_HOST)
                        file_path = os.path.join(settings.MEDIA_ROOT, str(path))
                        with open(file_path, 'rb') as f1:  # 判断文件的编码
                            data_type = chardet.detect(f1.readline())['encoding']
                        if data_type == 'None':
                            return Response({'msg': '数据格式有误', 'status': False})
                        os.renames(file_path, os.path.join(settings.MEDIA_ROOT, str(format_name)))
                        client.upload("/datahoop", os.path.join(settings.MEDIA_ROOT, str(format_name)), n_threads=4)
                        os.remove(os.path.join(settings.MEDIA_ROOT, str(format_name)))
                        try:
                            with client.read('/datahoop/' + str(format_name), encoding=data_type) as reader:
                                filesize = ((client.status('/datahoop/' + str(format_name)))['length']) / 1024
                                filesize = str(round(filesize, 2)) + 'KB'
                                reader = reader.readlines()
                        except:
                            return Response({'msg': '数据读取失败', 'status': False})
                        column_delimiter = separator
                        if is_header == 1:
                            title = (reader[0]).split(column_delimiter)
                            json = {}
                            s = ((reader[0]).split(column_delimiter))
                            for i in s:
                                json[i.replace('\r\n', '')] = [typ.StringType, True]
                            print(json)
                        else:
                            total = len((reader[0]).split(column_delimiter))
                            title = []
                            for i in range(total):
                                title.append('_C' + str(i))
                            json = {}
                            for i in title:
                                json[i] = [typ.StringType, True]

                        column_num = len((reader[0]).split(column_delimiter))
                        row_num = len(reader)
                        DataSource.objects.filter(format_filename=format_name).update(user_id=user,
                                                                                      title=title[:20],
                                                                                      fileSize=filesize,
                                                                                      where='hdfs', row_num=row_num,
                                                                                      column_num=column_num)
                        over_time = time.time()
                        print('ID为<%s>用户--数据上传<%s>文件的时间为--<%s>秒' % (user, format_name, over_time - start_time))
                        return Response({'msg': '数据存储成功', 'status': True})
                    else:
                        global object_id
                        filePath = os.path.join(settings.MEDIA_ROOT, str(path))
                        file_serializer.save()
                        filesize = str(round((path.size) / 1024, 2)) + 'KB'
                        if last == 'XLS' or last == 'XLSX':
                            pass
                        elif last == 'TXT':
                            object_id = tools.save_mongo_txt(filePath, user, is_header, separator, str(path))
                            if object_id != 'none':
                                file_serializer.validated_data['obj_id'] = object_id
                                file_serializer.validated_data['file_name'] = str(path)
                                file_serializer.save()
                            else:
                                DataSource.objects.filter(file_name=str(path), user=1).delete()
                                os.remove(os.path.join(settings.MEDIA_ROOT, str(path)))
                                return Response({'msg': '数据格式有误', 'status': False})
                        elif last == 'CSV':
                            object_id = tools.save_mongo_csv(filePath, user, is_header, separator, str(path))
                            if object_id != 'none':
                                file_serializer.validated_data['obj_id'] = object_id
                                file_serializer.validated_data['file_name'] = str(path)
                                file_serializer.save()
                            else:
                                # uuid = uuid.uuid1()
                                # file_serializer.validated_data['obj_id'] = uuid
                                # file_serializer.validated_data['file_name'] = str(path)
                                # file_serializer.save()

                                DataSource.objects.filter(file_name=str(path), user=1).delete()
                                os.remove(os.path.join(settings.MEDIA_ROOT, str(path)))
                                return Response({'msg': '数据格式有误', 'status': False})
                        elif last == 'SQL':
                            try:
                                object_id = tools.save_mongo_sql(filePath, user)
                                file_serializer.validated_data['obj_id'] = object_id
                                file_serializer.validated_data['file_name'] = str(path)
                                file_serializer.save()
                            except Exception as e:
                                DataSource.objects.filter(file_name=str(path), user=1).delete()
                                os.remove(os.path.join(settings.MEDIA_ROOT, str(path)))
                                return Response({'msg': '数据格式有误', 'status': False})
                        with open(filePath, 'rb') as f1:  # 判断文件的编码
                            data_type = chardet.detect(f1.readline())['encoding']
                        with open(filePath, encoding=data_type, errors='ignore') as reader:  # 按编码读文件
                            reader = reader.readlines()
                        if is_header == 1:
                            title = (reader[0]).split(separator)
                            json = {}
                            s = ((reader[0]).split(separator))
                            for i in s:
                                json[i.replace('\r\n', '')] = [typ.StringType, True]
                            column_num = len((reader[0]).split(separator))
                        else:
                            if last != 'SQL':
                                total = len((reader[0]).split(separator))
                                title = []
                                for i in range(total):
                                    title.append('_C' + str(i))
                                json = {}
                                for i in title:
                                    json[i] = [typ.StringType, True]
                                column_num = len((reader[0]).split(separator))
                            else:
                                total = re.findall(r'[^()]+', reader[0])[1].split(',')
                                title = []
                                for i in range(len(total)):
                                    title.append('_C' + str(i))
                                json = {}
                                for i in title:
                                    json[i] = [typ.StringType, True]
                                column_num = len(total)
                        row_num = len(reader)
                        DataSource.objects.filter(obj_id=object_id).update(user_id=user, title=title[:20],
                                                                           fileSize=filesize, where='mongodb',
                                                                           row_num=row_num, column_num=column_num)
                        os.remove(os.path.join(settings.MEDIA_ROOT, str(path)))
                        over_time = time.time()
                        print('ID为<%s>用户--数据上传<%s>文件的时间为--<%s>秒' % (user, path, over_time - start_time))
                        return Response({'msg': '数据存储成功', 'status': True})
                else:
                    return Response({'msg': '暂不支持此类文件上传', 'status': False})
        else:
            return Response({'msg': '不是一个有效的数据', 'status': False})

    # 获取文件列表
    def get(self, request, *args, **kwargs):
        # print(request.data)
        action = request.query_params.get('label_name')
        page = request.query_params.get('page')
        page = int(page)
        json_list = []
        # (1, "商业"),(2, "文化"),(3, "环境"),(4, "生活"),(5, "社会"),(6, "体育"),(7, "教育"),(8, "科技"),(9, "时政")
        data_label = {
            "商业": 1, "文化": 2, "环境": 3, "生活": 4, "社会": 5, "体育": 6, "教育": 7, "科技": 8, "时政": 9
        }
        if len(eval(action)) != 0:
            data_list = []
            # [<QuerySet [<DataSource: >, <DataSource: >, <DataSource: >]>, <QuerySet []>, <QuerySet []>]
            for i in eval(action):
                file = DataSource.objects.filter(parent=data_label[i], share_status=0)
                data_list.append(file)
            x = []
            for i in data_list:
                for l in i:
                    x.insert(0, l)
            files_list = x[page * 15 - 15:page * 15]
            sum = len(x)
        else:
            #  <QuerySet [<DataSource: >, <DataSource: >, <DataSource: >]>
            file = DataSource.objects.filter(share_status=0).all()
            sum = file.count()
            file = file[::-1]
            files_list = file[page * 15 - 15:page * 15]
        for file in files_list:
            json_dict = {}
            if file.create_time.date() == datetime.datetime.now().date():
                json_dict['isnew'] = 'yes'
            else:
                json_dict['isnew'] = 'no'
            json_dict['price'] = file.price
            json_dict['header'] = '/media/' + str(file.user.image.url)
            json_dict['user'] = file.user.username
            json_dict['id'] = file.id
            json_dict['file_name'] = str(file.file_name)
            json_dict['title'] = file.detail
            json_dict['fav_num'] = file.fav_num
            json_dict['where'] = file.where
            json_dict['view_num'] = file.view_num
            json_dict['download_num'] = file.download_num
            json_dict['thumb_num'] = file.thumb_num
            json_dict['label'] = [file.label_name, '']
            json_list.append(json_dict)
            # json.dumps(json_list)
        return_json = {'status': True, 'data': json_list, 'sum': sum, 'msg': '返回成功'}
        return HttpResponse(json.dumps(return_json), content_type='application/json')

    def delete(self, request, *args, **kwargs):

        file_id = request.data.get('file_id')
        where = DataSource.objects.get(id=file_id).where
        if where == 'hdfs':
            file = DataSource.objects.get(id=file_id)
            hdfs_name = DataSource.objects.get(id=file_id).format_filename
            client = Client(HDFS_HOST)
            client.delete('/datahoop/' + hdfs_name, recursive=True)
            file.delete()
        else:
            client = pymongo.MongoClient(settings.MONGO_DB_HOST, settings.MONGO_DB_PORT)
            db = client.datahoop.data
            file_id = DataSource.objects.filter(id=id).first()
            obj_id = file_id.obj_id
            file_id.delete()
            db.remove({"_id": ObjectId(obj_id)})
            client.close()
        return HttpResponse(content_type='application/json')


class DetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, detail_id):
        id = detail_id
        view_num = DataSource.objects.get(id=id).view_num
        DataSource.objects.filter(id=id).update(view_num=view_num + 1)
        user_id = request.user.id
        object = DataSource.objects.get(id=id)
        where = object.obj_id
        if where == '':
            try:
                file = object.format_filename
                file = str(file)
                header = 'media/' + str(object.user.image)
                username = object.user.username
                hdfs_path = '/datahoop/' + file
                client = Client(HDFS_HOST)
                json = {}
                json['header'] = header

                file_user_id = object.user.id
                relation = Relationship.objects.filter(author_id=user_id)
                all = []
                for i in relation:
                    all.append(i.User_ByID)
                if str(file_user_id) in all:
                    json['is_focus'] = 1
                else:
                    json['is_focus'] = 0

                objects = Collect.objects.filter(source=1, user=user_id, file_id=id)
                if objects:
                    json['is_collect'] = 1
                else:
                    json['is_collect'] = 0
                love = Love.objects.filter(user=user_id, file_id=id, source=1)
                if love:
                    json['is_love'] = 1
                else:
                    json['is_love'] = 0
                file_user_id = object.user_id
                if user_id == file_user_id:
                    json['is_me'] = 1
                else:
                    json['is_me'] = 0
                json['file_name'] = str(object.file_name)
                json['title'] = object.detail

                json['hdfs'] = object.format_filename
                json['fav_num'] = object.fav_num
                json['view_num'] = object.view_num
                json['thumb_num'] = object.thumb_num
                json['label'] = [object.label_name, '']
                json['username'] = username
                json['data'] = []
                with client.read(hdfs_path, encoding='utf-8') as reader:
                    for i in (reader.readlines())[0:20]:
                        print(i)
                        json['data'].append(i.split(','))
                return Response(json, status=status.HTTP_200_OK)
            except Exception as  e:
                print(e)
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                client = pymongo.MongoClient(MONGO_DB_URI)
                db = client.datahoop.data
                json = {}
                fileName = str(object.file_name)
                obj_id = object.obj_id
                file_user_id = object.user.id
                relation = Relationship.objects.filter(author_id=user_id)
                all = []
                for i in relation:
                    all.append(i.User_ByID)
                if str(file_user_id) in all:
                    json['is_focus'] = 1
                else:
                    json['is_focus'] = 0

                result = db.find({'_id': ObjectId(obj_id)})
                fileType = (fileName.split('.')[-1]).lower()  # 获取文件后缀名
                table_name = fileName
                sheetList = ''
                sheet = ''
                json['file_user_id'] = file_user_id
                json['header'] = 'media/' + str(object.user.image)
                json['file_name'] = str(object.file_name)
                if user_id == file_user_id:
                    json['is_me'] = 1
                else:
                    json['is_me'] = 0
                json['title'] = object.detail
                objects = Collect.objects.filter(source=1, user=user_id, file_id=id)
                if objects:
                    json['is_collect'] = 1
                else:
                    json['is_collect'] = 0
                love = Love.objects.filter(user=user_id, file_id=id, source=1)
                if love:
                    json['is_love'] = 1
                else:
                    json['is_love'] = 0
                json['obj_id'] = object.obj_id
                json['fav_num'] = object.fav_num
                json['view_num'] = object.view_num
                json['thumb_num'] = object.thumb_num
                json['label'] = [object.label_name, '']
                json['username'] = object.user.username
                if fileType == 'xls' or fileType == 'xlsx':  # 读取ｅｘｃｅｌ文件　返回列表
                    sheetList = (sorted((result[0]['fileData'])))
                    rel = sorted((result[0]['fileData']).items())[0][1][0:501]
                    default_sheet = sorted((result[0]['fileData']).items())[0][0]
                    sheet = request.GET.get('sheet')
                    if sheet:
                        rel = (result[0]['fileData'][sheet][0:501])
                    else:
                        sheet = default_sheet
                elif fileType == 'csv' or fileType == 'txt':
                    import pandas as pd
                    # empty = pandas.DataFrame()
                    # data = empty.append(result[0]['fileData'])
                    # rel = data[0:].values.tolist()[0:20]
                    data = pd.DataFrame(result[0]['fileData'])
                    rel = data.values.tolist()[0:200]
                    for i in range(len(rel)):
                        for j in range(len(rel[i])):
                            if str(rel[i][j]) == "nan":
                                rel[i][j] = ""
                    json['data'] = rel
                elif fileType == 'sql':
                    rel = (result[0]['fileData'])[0:20]
                    json['data'] = rel
                client.close()
                return Response(json, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return Response(status=status.HTTP_404_NOT_FOUND)


class Collect_View(APIView):
    def get(self, request):
        try:
            file_id = request.GET.get('file_id')

            action = request.GET.get('action')
            action = int(action)
            user = request.user.id
            Collect.objects.create(user_id=user, file_id=file_id, source=action)
            fav_num = DataSource.objects.get(id=file_id).fav_num
            DataSource.objects.filter(id=file_id).update(fav_num=fav_num + 1)
            return JsonResponse({'status': True})
        except:
            JsonResponse({'status': False})

    def delete(self, request, *args, **kwargs):
        try:
            user = request.user.id
            file_id = request.data.get('file_id')
            action = request.data.get('action')
            Collect.objects.filter(file_id=file_id, user_id=user, source=action).delete()
            thum = DataSource.objects.get(id=file_id).thumb_num
            DataSource.objects.filter(id=file_id).update(thumb_num=thum - 1)
            return JsonResponse({'status': True})
        except:
            return JsonResponse({'status': False})


class LoveView(APIView):
    def get(self, request):
        try:
            file_id = request.GET.get('file_id')
            action = request.GET.get('action')
            user = request.user.id
            Love.objects.create(user_id=user, file_id=file_id, source=action)
            thum = DataSource.objects.get(id=file_id).thumb_num
            DataSource.objects.filter(id=file_id).update(thumb_num=thum + 1)
            return JsonResponse({'status': True})
        except:
            return JsonResponse({'status': False})

    def delete(self, request, *args, **kwargs):
        try:
            user = request.user.id
            file_id = request.data.get('file_id')
            action = request.data.get('action')
            Love.objects.filter(file_id=file_id, user_id=user, source=action).delete()
            thum = DataSource.objects.get(id=file_id).thumb_num
            DataSource.objects.filter(id=file_id).update(thumb_num=thum - 1)
            return JsonResponse({'status': True})
        except:
            return JsonResponse({'status': False})


class SearchView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        content = request.query_params.get('content')
        page = request.query_params.get('page')
        page = int(page)
        # file = DataSource.objects.filter(Q(Q(file_name__icontains=content)|Q(lable.name__icontains=content)))
        file = DataSource.objects.filter(
            Q(label_name__icontains=content, share_status=0) | Q(file_name__icontains=content, share_status=0))
        sum = file.count()
        json_list = []
        files_list = file[page * 15 - 15:page * 15]
        for file in files_list:
            json_dict = {}
            # json_dict['file_name']=file.file_name
            json_dict['file_name'] = str(file.file_name)
            json_dict['title'] = file.title
            json_dict['download_num'] = file.download_num
            json_dict['view_num'] = file.view_num
            json_dict['thumb_num'] = file.thumb_num
            json_dict['price'] = file.price
            json_dict['label'] = [file.label_name]
            json_list.append(json_dict)
            json.dumps(json_list)

        return_json = {'status': True, 'data': json_list, 'sum': sum, 'msg': '返回成功'}
        return HttpResponse(json.dumps(return_json), content_type='application/json')
        # return Response(json_list, status=200)


class ThirdView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):

        user = request.user.id
        action = request.query_params.get('action')
        page = request.query_params.get('page')
        page = int(page)
        json_list = []
        if action:
            file = DataSource.objects.filter(parent=action, share_status=0, user_id=1)
        else:
            file = DataSource.objects.filter(share_status=0, user_id=1)
        sum = file.count()
        is_mine = DataSource.objects.filter(user_id=user)
        mine = []
        for i in is_mine:
            mine.append(i.file_name)
        files_list = file[page * 15 - 15:page * 15]
        for file in files_list:
            json_dict = {}
            if file.create_time.date() == datetime.datetime.now().date():
                json_dict['isnew'] = 'yes'
            else:
                json_dict['isnew'] = 'no'
            if file.file_name in mine:
                json_dict['is_mine'] = 1
            else:
                json_dict['is_mine'] = 0
            json_dict['header'] = '/media/' + str(file.user.image.url)
            json_dict['user'] = file.user.username
            json_dict['id'] = file.id
            json_dict['where'] = file.where
            json_dict['file_name'] = str(file.file_name)
            json_dict['title'] = file.detail
            json_dict['fav_num'] = file.fav_num
            json_dict['view_num'] = file.view_num
            json_dict['download_num'] = file.download_num
            json_dict['thumb_num'] = file.thumb_num
            json_dict['label'] = [file.label_name, '']
            json_dict['sum'] = sum
            json_list.append(json_dict)
            json.dumps(json_list)

        return Response(json_list, status=200)


#  添加至我的数据
class Add_Data(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        mg_client = pymongo.MongoClient(MONGO_DB_URI)
        db = mg_client.datahoop.data
        id = request.user.id
        try:
            file_id = request.GET.get('file_id')
            obj = DataSource.objects
            object_id = DataSource.objects.get(id=file_id).obj_id
            fileName = DataSource.objects.get(id=file_id).file_name
            data = db.find_one({'_id': ObjectId(object_id)})['fileData']
            jsonData = {
                'fileName': str(fileName),
                'userID': id,
                'fileData': data
            }

            object_id = db.insert(jsonData)
            object_id = string_type(object_id)
            mg_client.close()
            obj.create(user_id=id, file_name=str(fileName), where='mongodb', obj_id=object_id)
            return JsonResponse({'status': True, 'msg': '添加成功'})
        except Exception as e:
            print(e)
            return JsonResponse({'status': False, 'msg': '添加失败,已添加！'})


#  批量添加到我的数据
class Add_More_Data(APIView):
    '''
    批量添加至我的数据
    '''
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        mg_client = pymongo.MongoClient(MONGO_DB_URI)
        db = mg_client.datahoop.data
        id = request.user.id
        try:
            all_file_id = request.GET.get('file_id')
            all_file_id = eval(all_file_id)
            obj = DataSource.objects
            try:
                for file_id in all_file_id:
                    fileName = DataSource.objects.get(id=file_id).file_name

                    if DataSource.objects.get(id=file_id).where == 'mongodb':
                        object_id = DataSource.objects.get(id=file_id).obj_id

                        data = db.find_one({'_id': ObjectId(object_id)})['fileData']
                        jsonData = {
                            'fileName': str(fileName),
                            'userID': id,
                            'fileData': data
                        }
                        object_id = db.insert(jsonData)
                        object_id = string_type(object_id)
                        mg_client.close()
                        obj.create(user_id=id, file_name=str(fileName), where='mongodb', obj_id=object_id)
                    else:
                        format_filename = DataSource.objects.get(id=file_id).format_filename
                        obj.create(user_id=id, file_name=str(fileName), format_filename=format_filename, where='hdfs')
            except Exception as  e:
                return JsonResponse({'status': False, 'msg': '添加失败'})
            return JsonResponse({'status': True, 'msg': '添加成功'})
        except Exception as e:
            print(e)
            return JsonResponse({'status': False, 'msg': '添加失败'})


class MysqlDatabaseView(APIView):
    """
    mysql database connect
    """
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        host = request.data.get('host')
        port = request.data.get('port')
        database_name = request.data.get('database_name')
        request.session['username'] = username
        request.session['password'] = password
        request.session['host'] = host
        request.session['port'] = port
        request.session['database_name'] = database_name
        db = pymysql.connect(host, username, password, database_name)
        cursor = db.cursor()
        sql = "show tables ;"
        l = []
        for i in (cursor.fetchmany(cursor.execute(sql))):
            l.append(i[0])
        cursor.close()
        db.close()
        return HttpResponse(json.dumps(l), content_type='application/json')

    def get(self, request, *args, **kwargs):
        # table_name = request.data.get('name')
        table_name = 'files_datasource'
        username = request.session['username']
        password = request.session['password']
        host = request.session['host']
        port = request.session['port']
        database_name = request.session['database_name']
        obj = DataSource.objects
        con = pymysql.connect(host, username, password, database_name)
        client = Client(HDFS_HOST)
        cur = con.cursor()
        # for i in table_name:
        sql = "select DISTINCT (COLUMN_NAME) from information_schema.COLUMNS where table_name = '%s'"
        cur.execute(sql % (table_name))
        rows = cur.fetchall()
        rels = []
        rel = []
        for i in rows:
            rel.append(i[0])
        rels.append(rel)  # 类似于其他语言的 query 函数， execute 是 python 中的执行查询函数
        cur.execute("SELECT * FROM  %s" % (table_name))  # 使用 fetchall 函数，将结果集（多维元组）存入 rows 里面
        rows = cur.fetchall()  # 依次遍历结果集，发现每个元素，就是表中的一条记录，用一个元组来显示
        for row in rows:
            rels.append(list(row))
        file_name = table_name + '.sql'
        format_name = uuid.uuid1()
        filepath = settings.MEDIA_ROOT + str(format_name)
        with open(filepath, 'wb+') as writer:
            for chunk in rels:
                writer.write(chunk)

        client.upload("/datahoop", filepath)
        obj.create(file_name=file_name, format_name=format_name, user_id=1)
        os.remove(filepath)
        client.close()
        con.close()
        cur.close()

        return HttpResponse(json.dumps(rels), content_type='application/json')


class PostgresqlDatabaseView(APIView):
    """
    postgresql database connect
    """
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        host = request.data.get('host')
        port = request.data.get('port')
        database_name = request.data.get('database_name')
        request.session['username'] = username
        request.session['password'] = password
        request.session['host'] = host
        request.session['port'] = port
        request.session['database_name'] = database_name
        conn = psycopg2.connect(database=database_name, user=username, password=password, host=host, port=port)
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'; ")
        l = []
        for i in (cur.fetchall()):
            s = (str(i).replace("(", '').replace(")", '').replace(",", '')).replace("'", '')
            l.append(s)
        cur.close()
        conn.close()
        return HttpResponse(json.dumps(l), content_type='application/json')

    def get(self, request, *args, **kwargs):
        table_name = request.data.get('name')
        username = request.session['username']
        password = request.session['password']
        host = request.session['host']
        port = request.session['port']
        database_name = request.session['dbdatabase_name']
        obj = DataSource.objects
        conn = psycopg2.connect(database=database_name, user=username, password=password, host=host, port=port)
        client = Client(HDFS_HOST)
        cur = conn.cursor()
        for i in table_name:
            global rels
            cur.execute("select COLUMN_NAME from information_schema.COLUMNS where table_name = '%s'" % ())
            rels = []
            rel = []
            rows = cur.fetchall()
            for i in rows:
                a = ((str(i).replace("(", '').replace(")", '').replace(",", '')).replace("'", ''))
                rel.append(a)
            rels.append(rel)  # 类似于其他语言的 query 函数， execute 是 python 中的执行查询函数
            cur.execute("SELECT * FROM  %s" % (i))  # 使用 fetchall 函数，将结果集（多维元组）存入 rows 里面
            rows1 = cur.fetchall()  # 依次遍历结果集，发现每个元素，就是表中的一条记录，用一个元组来显示
            for row in rows1:
                rels.append(list(row))
            file_name = i + '.sql'
            format_name = uuid.uuid1()
            filepath = settings.MEDIA_ROOT + format_name
            with open(filepath, 'wb+') as writer:
                for chunk in rels:
                    writer.write(chunk)

            client.upload("/datahoop", filepath)
            obj.create(file_name=file_name, format_name=format_name, user_id=1)
            os.remove(filepath)
        client.close()
        cur.close()
        conn.close()

        return HttpResponse(json.dumps(rels), content_type='application/json')


class SqlserverDatabaseView(APIView):
    """sqlserver database connect"""
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        host = request.data.get('host')
        port = request.data.get('port')
        database_name = request.data.get('database_name')
        request.session['username'] = username
        request.session['password'] = password
        request.session['host'] = host
        request.session['port'] = port
        request.session['database_name'] = database_name
        try:
            conn = pymssql.connect(database=database_name, user=username, password=password, host=host, port=port)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM SysObjects Where XType='U' ORDER BY Name")
            global list
            list = []
            for i in (cursor.fetchall()):
                for item in i:
                    list.append(item)
            cursor.close()
            conn.close()
            return HttpResponse(json.dumps(list), content_type='application/json')
        except:
            return HttpResponse({'status': 404, 'msg': '数据库地址或密码输入有误！'})

    def get(self, request, *args, **kwargs):
        table_name = request.data.get('name')
        username = request.session['username']
        password = request.session['password']
        host = request.session['host']
        port = request.session['port']
        database_name = request.session['dbdatabase_name']
        obj = DataSource.objects
        conn = pymssql.connect(database=database_name, user=username, password=password, host=host, port=port)
        client = Client(HDFS_HOST)
        cur = conn.cursor()
        for i in table_name:
            global rels
            cur.execute("select name from syscolumns where id = object_id('%s');" % (i))
            rels = []
            rel = []
            rows = cur.fetchall()
            for i in rows:
                for item in i:
                    rel.append(item)
            rels.append(rel)
            # 类似于其他语言的 query 函数， execute 是 python 中的执行查询函数
            cur.execute("SELECT * FROM  %s" % (i))
            # 使用 fetchall 函数，将结果集（多维元组）存入 rows 里面
            rows1 = cur.fetchall()
            # 依次遍历结果集，发现每个元素，就是表中的一条记录，用一个元组来显示
            for row in rows1:
                rels.append(list(row))
            file_name = i + '.sql'
            format_name = uuid.uuid1()
            filepath = settings.MEDIA_ROOT + format_name
            with open(filepath, 'wb+') as writer:
                for chunk in rels:
                    writer.write(chunk)

            client.upload("/datahoop", filepath)
            obj.create(file_name=file_name, format_name=format_name, user_id=1)
            os.remove(filepath)
        client.close()
        cur.close()
        conn.close()

        return HttpResponse(json.dumps(rels), content_type='application/json')


class IntoDatabase(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        file_serializer = ExcelDatasourceSerializer(data=request.data)
        if file_serializer.is_valid():
            file = file_serializer.validated_data['file_name']
            file_serializer.save()
            print(file.read())
            print(file.size)
            print(type(str(file)))
            return Response(file_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'msg': file_serializer.errors, 'status': False}, status=status.HTTP_200_OK)


class Download_Hdfs(APIView):
    def get(self, request):
        client = Client(HDFS_HOST)
        hdfs = request.GET.get('hdfs')
        file_name = DataSource.objects.get(format_filename=hdfs).file_name
        client.download('/datahoop/' + hdfs, settings.MEDIA_ROOT + 'hdfs_download')
        path = os.path.join(settings.MEDIA_ROOT, 'hdfs_download')
        file = open(os.path.join(path, hdfs), 'rb')
        response = FileResponse(file)
        response = HttpResponse(content_type='application/vnd.ms-csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(file_name.split('.')[0])
        return (response)


class From_Superstar(APIView):
    """接收来自超星的课程信息，并保存到数据库"""

    def post(self, request):
        try:
            key = request.data['key']
            if key == "44bbf3b8db6395274aadb9e6071769ea":
                # wecoursefromchaoxing的md5加密32位,https://md5jiami.51240.com/
                content = request.data['content']
                for i in content:
                    if not WeCourse.objects.filter(name=i[0]):
                        WeCourse.objects.create(name=i[0], label=i[1], price=i[2], abstract=i[3])
                        return_json = {'status': True, 'data': '%s 课程信息创建成功' % (i[0]), 'msg': '秘钥正确'}
                    else:
                        WeCourse.objects.filter(name=i[0]).update(name=i[0], label=i[1], price=i[2], abstract=i[3])
                        return_json = {'status': True, 'data': '%s课程已更新' % (i[0]), 'msg': '秘钥正确'}
            else:
                return_json = {'status': False, 'data': '课程信息创建失败', 'msg': '秘钥错误'}
        except:
            return_json = {'status': False, 'data': '课程信息创建失败', 'msg': '缺少秘钥'}
        return HttpResponse(json.dumps(return_json), content_type='application/json')


class Course_Detail(APIView):
    """
    "id": 1,
        "name": "",
        "label": "",
        "abstract": "",
        "content": "数",
        "cover": "/media/files/cover/QQ%E6%88%AA%E5%9B%BE20180410102337.jpg",
        "main_push": 1,
        "view_num": 0,
        "thumb_num": 0,
        "is_buy": false,
        "price": 368.0,
        "create_time": "2018-04-10T10:24:25.526285"
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            course_id = request.GET.get('course_id')
            view = WeCourse.objects.get(id=course_id).view_num
            WeCourse.objects.filter(id=course_id).update(view_num=view + 1)
            wecourses = WeCourse.objects.get(id=course_id)
        except:
            wecourses = WeCourse.objects.all()

        wecourses_serializer = WeCourseSerializer(wecourses, many=True)

        return Response(wecourses_serializer.data)
