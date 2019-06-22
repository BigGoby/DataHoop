# -*- coding: utf-8 -*-
import os
import pymongo
import re
import json
import pandas as pd
import xlwt

from bson import json_util
from .excel_fun import Stats
from hdfs import *
from rest_framework.views import APIView
from django.shortcuts import HttpResponse
from files.models import DataSource
from collections import Counter
from django.conf import settings
from bson.objectid import ObjectId
from bson.objectid import string_type
from rest_framework.permissions import IsAuthenticated
from personalcenter.models import Collect
from rest_framework.decorators import api_view
from io import BytesIO
from utils.logConf import log

logger = log(__name__)

mg_client = pymongo.MongoClient(settings.MONGO_DB_URI)
db = mg_client.datahoop.data


# 获取文件名
class NameView(APIView):
    """
    获取文件名

    参数没有传空

    {

        type:get,

        url:/dispose/name/,

        data:{},

        dataType:JSON,
    }
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        thumb = DataSource.objects.filter(user=request.user.id).all().order_by('-create_time')
        name = []
        for i in thumb:
            dic = {}
            dic[str(i.file_name)] = i.id
            name.append(dic)
        return_json = {'status': True, 'data': name, 'msg': '获取文件名成功'}
        logger.info("用户:{0}获取文件名".format(request.user))
        return HttpResponse(json.dumps(return_json), content_type='application/json')


# 获取数据
class FileView(APIView):
    """
    获取数据

    参数没有传空

    {

        type:post,

        url:/dispose/file/,

        data:{uuid:文件的id(uuid),},

        dataType:JSON,

    }
    """

    # def get(self, request):
    #     pass

    def post(self, request):
        uuid = request.POST.get('uuid', 96)
        if uuid == '':
            return_json = {'status': True, 'data': None, 'msg': '没有接收到文件id'}
            return HttpResponse(json.dumps(return_json), content_type='application/json')
        else:
            if DataSource.objects.get(id=uuid).obj_id != '':
                return_json = {'status': True, 'data': None, 'msg': '文件读取成功，文件信息已存入MySQL'}
                logger.info("文件{0}的信息存入MySQL成功".format(uuid))
                return HttpResponse(json.dumps(return_json), content_type='application/json')
            else:
                p = os.path.join(settings.BASE_DIR, "media")
                uuid = DataSource.objects.get(id=uuid).format_filename
                path = os.path.join('/datahoop/', uuid)
                path1 = os.path.join(p, uuid)

                client = Client(settings.HDFS_HOST)
                client.download(path, p)
                file_name = DataSource.objects.get(format_filename=uuid).file_name
                file_name = str(file_name)
                if re.search("\.(\w+)$", file_name).group() in ['.txt', '.csv', '.sql', '.html']:
                    data = []
                    try:
                        file = open(path1, 'r', encoding="utf-8")
                        while 1:
                            lines = file.readlines()
                            if not lines:
                                break
                            for line in lines:
                                data.append(line.split(','))
                    except:
                        # with open(path1, 'rb') as f1:  # 判断文件的编码
                        #     data_type = chardet.detect(f1.readline())['encoding']
                        file = open(path1, 'r', encoding="GBK")
                        while 1:
                            lines = file.readlines()
                            if not lines:
                                break
                            for line in lines:
                                data.append(line.split(','))

                    content = {'userID': request.user.id,
                               'fileData': data,
                               'fileName': file_name,
                               }
                    obj_id = db.insert(content)
                    obj_id = string_type(obj_id)
                    dataframe = pd.DataFrame(data)
                    row = dataframe.columns.size
                    col = dataframe.iloc[:, 0].size
                    title = data[0]
                    os.remove(path1)
                    DataSource.objects.filter(format_filename=uuid).update(obj_id=obj_id, row_num=int(row),
                                                                           column_num=int(col), )
                    return_json = {'status': True, 'data': None, 'msg': '文件读取成功，文件信息已存入MySQL'}
                    logger.info("文件{0}的信息存入MySQL成功".format(uuid))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                else:
                    return_json = {'status': True, 'data': None, 'msg': '文件无法处理'}
                    logger.error("文件{0}无法处理".format(uuid))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                    # else:
                    #     return_json = {'status': True, 'data': None, 'msg': '文件读取成功，文件信息已存入MySQL'}
                    #     logger.info("文件{0}的信息存入MySQL成功".format(uuid))
                    #     return HttpResponse(json.dumps(return_json), content_type='application/json')


# 显示数据
class ShowDetailView(APIView):
    """
    显示数据内容

    参数没有传空

    {

        type:get,

        url:/dispose/detail/,

        data:{num:当前页码,

              file_num:合并表的数量，

              title1:第一个选择框左侧的key值，

              title2:第一个选择框右侧的key值，

              title3_l:第二个选择框左侧的key值，

              title3_r:第二个选择框右侧的key值，

              title4_l:第三个选择框左侧的key值，

              title4_r:第三个选择框右侧的key值，

              type:合并方式。外部：outer，左侧：left，右侧：right，内链接：inner，

              type2:同上。第二个合并方式

              type3:同上。第三个合并方式

              click_file:点击第一个文件的id,

              click_file2:点击第二个文件的id,

              click_file3:点击第三个文件的id,

              click_file4:点击第四个文件的id,

              },

        dataType:JSON,
    }
    """

    def get(self, request):
        num = int(request.GET.get('num', 1))
        click_file = request.GET.get('click_file', 1)
        click_file2 = request.GET.get('click_file2', 1)
        click_file3 = request.GET.get('click_file3', 1)
        click_file4 = request.GET.get('click_file4', 1)
        obj_id = request.GET.get('obj_id')
        file_num = request.GET.get('file_num', 1)
        if file_num == '':
            file_num = 1
        else:
            file_num = int(file_num)
        try:
            obj_id1 = (DataSource.objects.filter(id=int(click_file)).all())[0].obj_id
            un_data = db.find({'_id': ObjectId(obj_id1)})[0]['fileData']
            if db.find_one({'userID': request.user.id, 'un_name': '初始数据'}):
                db.update({'userID': request.user.id, 'un_name': '初始数据'}, {'$set': {'un_data': un_data}})
            else:
                db.insert({'userID': request.user.id, 'un_name': '初始数据', 'un_data': un_data})
        except:
            pass
        # 下一步数据
        if file_num == 0:
            uuid = request.GET.get('uuid')
            result = (db.find({'_id': ObjectId(obj_id)}))
            filename = (DataSource.objects.filter(obj_id=obj_id))[0].file_name
            if re.search("\.(\w+)$", str(filename)).group() in ['.sql']:
                data = result[0]['fileData']
                for i in range(len(data)):
                    data[i] = list(map(str, data[i]))
                db.update({'_id': ObjectId(obj_id)}, {'$set': {'fileData': data}})
            result = (db.find({'_id': ObjectId(obj_id)}))
            filename = str((DataSource.objects.filter(obj_id=obj_id))[0].file_name)
            if re.search("\.(\w+)$", filename).group() in ['.txt', '.csv', '.CSV', '.TXT', '.sql']:
                empty = pd.DataFrame()
                data = empty.append(result[0]['fileData'])
            if len(data) / 10 == 1:
                amount = 1
            elif (len(data) / 10) < 0:
                amount = 1
            else:
                amount = (len(data) // 10) + 1
            if amount < 1:
                result_data = data[0:].values.tolist()
            elif num == 1:
                result_data = data[0:11].values.tolist()
            else:
                result_data = data[(num * 10 - 9):(num * 10 + 1)].values.tolist()
            file_data = json_util.loads(json_util.dumps(result_data))
            return_json = {'status': True,
                           'data': file_data,
                           'amount': amount,
                           'click_file': filename,
                           'msg': '获取成功',
                           }
            logger.info("文件{0}数据读取成功".format(uuid))
            return HttpResponse(json.dumps(return_json), content_type='application/json')

        # 拖拽数据
        else:
            if file_num == 2:
                obj_id2 = (DataSource.objects.filter(id=int(click_file2)).all())[0].obj_id
                try:
                    my_type = request.GET.get('type', '')
                    key1 = request.GET.get('title1', '')
                    key2 = request.GET.get('title2', '')
                    result1 = db.find({'_id': ObjectId(obj_id1)})

                    mydata1 = result1[0]['fileData']

                    title1 = json_util.loads(json_util.dumps(mydata1[0]))
                    result2 = db.find({'_id': ObjectId(obj_id2)})
                    mydata2 = result2[0]['fileData']
                    title2 = json_util.loads(json_util.dumps(mydata2[0]))
                    biaotou1 = mydata1[0]
                    biaotou2 = mydata2[0]
                    mydata1 = pd.DataFrame(mydata1[1:], columns=biaotou1)
                    mydata2 = pd.DataFrame(mydata2[1:], columns=biaotou2)

                    if key1 and key2:
                        try:
                            result = (pd.merge(mydata1, mydata2, left_on=key1, right_on=key2, how=my_type)).fillna('')
                            biaotou = list(result.columns)
                            merge_data = [biaotou] + result.values.tolist()
                            if (db.find_one({'userID': request.user.id, 'merge_name': '合并数据'})):
                                db.update({'userID': request.user.id, 'merge_name': '合并数据'},
                                          {'$set': {'fileData': merge_data}})
                            else:
                                db.insert({'userID': request.user.id, 'merge_name': '合并数据', 'fileData': merge_data})

                            try:
                                if db.find_one({'userID': request.user.id, 'un_merge_name': '初始合并数据'}):
                                    db.update({'userID': request.user.id, 'un_merge_name': '初始合并数据'},
                                              {'$set': {'un_data': merge_data}})
                                else:
                                    db.insert(
                                        {'userID': request.user.id, 'un_merge_name': '初始合并数据', 'un_data': merge_data})
                            except:
                                pass

                            if len(merge_data) % 10 == 0:
                                amount = (len(merge_data) / 10)
                            else:
                                amount = (len(merge_data) // 10) + 1
                            if amount < 1:
                                result_data = merge_data[0:]
                            elif num == 1:
                                result_data = merge_data[0:11]
                            else:
                                result_data = merge_data[(num * 10 - 9):(num * 10 + 1)]
                            new_data = json_util.loads(json_util.dumps(result_data))
                            for i in range(len(new_data)):
                                new_data[i] = list(map(str, new_data[i]))
                            return_json = {'status': True,
                                           'data': new_data,
                                           'title1': title1,
                                           'title2': title2,
                                           'amount': amount,
                                           'msg': '获取合并数据成功',
                                           }
                            logger.info("文件{0}，{1}的数据合并读取成功".format(click_file, click_file2))
                            return HttpResponse(json.dumps(return_json), content_type='application/json')
                        except Exception as e:

                            return_json = {'status': True,
                                           'data': None,
                                           'title1': title1,
                                           'title2': title2,
                                           'amount': None,
                                           'msg': '获取表头成功',
                                           }
                            logger.info("文件{0}，{1}的数据合并读取成功".format(click_file, click_file2))
                            return HttpResponse(json.dumps(return_json), content_type='application/json')
                    else:
                        return_json = {'status': True,
                                       'data': None,
                                       'title1': title1,
                                       'title2': title2,
                                       'amount': None,
                                       'msg': '获取表头成功',
                                       }
                        logger.error("文件{0}，{1}的数据合并读取失败:参数不够".format(click_file, click_file2))
                        return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': True, 'data': None, 'msg': '失败'}
                    logger.error("文件{0}，{1}的数据合并读取失败：{2}".format(click_file, click_file2, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            elif file_num == 3:
                obj_id2 = (DataSource.objects.filter(id=int(click_file2)).all())[0].obj_id
                obj_id3 = (DataSource.objects.filter(id=int(click_file3)).all())[0].obj_id
                try:
                    my_type = request.GET.get('type')
                    my_type2 = request.GET.get('type2')

                    key1 = request.GET.get('title1')
                    key2 = request.GET.get('title2')
                    key3_l = request.GET.get('title3_l')
                    key3_r = request.GET.get('title3_r')

                    result1 = db.find({'_id': ObjectId(obj_id1)})
                    mydata1 = result1[0]['fileData']

                    result2 = db.find({'_id': ObjectId(obj_id2)})
                    mydata2 = result2[0]['fileData']

                    result3 = db.find({'_id': ObjectId(obj_id3)})
                    mydata3 = result3[0]['fileData']

                    biaotou1 = mydata1[0]
                    biaotou2 = mydata2[0]
                    biaotou3 = mydata3[0]
                    mydata1 = pd.DataFrame(mydata1[1:], columns=biaotou1)
                    mydata2 = pd.DataFrame(mydata2[1:], columns=biaotou2)
                    mydata3 = pd.DataFrame(mydata3[1:], columns=biaotou3)

                    if key1 and key2 and key3_r:
                        try:
                            result = (pd.merge(mydata1, mydata2, left_on=key1, right_on=key2, how=my_type)).fillna('')
                            result = pd.DataFrame(result[1:], columns=biaotou1 + biaotou2)
                            result = (pd.merge(result, mydata3, left_on=key3_l, right_on=key3_r, how=my_type2)).fillna(
                                '')

                            merge_data = result.values.tolist()
                            if (db.find_one({'userID': request.user.id, 'merge_name': '合并数据'})):
                                db.update({'userID': request.user.id, 'merge_name': '合并数据'},
                                          {'$set': {'fileData': merge_data}})
                            else:
                                db.insert({'userID': request.user.id, 'merge_name': '合并数据', 'fileData': merge_data})

                            try:
                                if db.find_one({'userID': request.user.id, 'un_merge_name': '初始合并数据'}):
                                    db.update({'userID': request.user.id, 'un_merge_name': '初始合并数据'},
                                              {'$set': {'un_data': merge_data}})
                                else:
                                    db.insert(
                                        {'userID': request.user.id, 'un_merge_name': '初始合并数据', 'un_data': merge_data})
                            except:
                                pass

                            if len(result) % 10 == 0:
                                amount = (len(result) / 10)
                            else:
                                amount = (len(result) // 10) + 1
                            if amount < 1:
                                result_data = result[0:].values.tolist()
                            elif num == 1:
                                result_data = result[0:11].values.tolist()
                            else:
                                result_data = result[(num * 10 - 9):(num * 10 + 1)].values.tolist()
                            new_data = json_util.loads(json_util.dumps(result_data))
                            for i in range(len(new_data)):
                                new_data[i] = list(map(str, new_data[i]))
                            return_json = {'status': True,
                                           'data': new_data,
                                           'amount': amount,
                                           'msg': '获取合并数据成功',
                                           }
                            logger.info("文件{0}，{1},{2}的数据合并读取成功".format(click_file, click_file2, click_file3))
                            return HttpResponse(json.dumps(return_json), content_type='application/json')
                        except Exception as e:

                            return_json = {'status': True,
                                           'data': [],
                                           'amount': None,
                                           'msg': '获取合并数据成功'}
                            logger.info("文件{0}，{1},{2}的数据合并读取成功".format(click_file, click_file2, click_file3))
                            return HttpResponse(json.dumps(return_json), content_type='application/json')
                    else:
                        return_json = {'status': True,
                                       'data': None,
                                       'amount': None,
                                       'msg': '获取表头成功',
                                       }
                        logger.error("文件{0}，{1},{2}的数据合并读取失败：参数不够".format(click_file, click_file2, click_file3))
                        return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '失败'}
                    logger.error("文件{0}，{1},{2}的数据合并读取失败：{3}".format(click_file, click_file2, click_file3, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            elif file_num == 4:
                obj_id2 = (DataSource.objects.filter(id=int(click_file2)).all())[0].obj_id
                obj_id3 = (DataSource.objects.filter(id=int(click_file3)).all())[0].obj_id
                obj_id4 = (DataSource.objects.filter(id=int(click_file4)).all())[0].obj_id
                try:
                    my_type = request.GET.get('type')
                    my_type2 = request.GET.get('type2')
                    my_type3 = request.GET.get('type3')

                    key1 = request.GET.get('title1')
                    key2 = request.GET.get('title2')
                    key3_l = request.GET.get('title3_l')
                    key3_r = request.GET.get('title3_r')
                    key4_l = request.GET.get('title4_l')
                    key4_r = request.GET.get('title4_r')

                    result1 = db.find({'_id': ObjectId(obj_id1)})
                    mydata1 = result1[0]['fileData']

                    result2 = db.find({'_id': ObjectId(obj_id2)})
                    mydata2 = result2[0]['fileData']
                    title2 = json_util.loads(json_util.dumps(mydata2[0]))

                    result3 = db.find({'_id': ObjectId(obj_id3)})
                    mydata3 = result3[0]['fileData']

                    result4 = db.find({'_id': ObjectId(obj_id4)})
                    mydata4 = result4[0]['fileData']

                    biaotou1 = mydata1[0]
                    biaotou2 = mydata2[0]
                    biaotou3 = mydata3[0]
                    biaotou4 = mydata4[0]
                    mydata1 = pd.DataFrame(mydata1[1:], columns=biaotou1)
                    mydata2 = pd.DataFrame(mydata2[1:], columns=biaotou2)
                    mydata3 = pd.DataFrame(mydata3[1:], columns=biaotou3)
                    mydata4 = pd.DataFrame(mydata4[1:], columns=biaotou4)

                    if key1 and key2 and key3_r and key4_r:
                        try:
                            result = (pd.merge(mydata1, mydata2, left_on=key1, right_on=key2, how=my_type)).fillna('')
                            result = pd.DataFrame(result[1:], columns=biaotou1 + biaotou2)
                            result = (pd.merge(result, mydata3, left_on=key3_l, right_on=key3_r, how=my_type2)).fillna(
                                '')
                            result = pd.DataFrame(result[1:], columns=biaotou1 + biaotou2 + biaotou3)
                            result = (pd.merge(result, mydata4, left_on=key4_l, right_on=key4_r, how=my_type3)).fillna(
                                '')

                            merge_data = result.values.tolist()
                            if (db.find_one({'userID': request.user.id, 'merge_name': '合并数据'})):
                                db.update({'userID': request.user.id, 'merge_name': '合并数据'},
                                          {'$set': {'fileData': merge_data}})
                            else:
                                db.insert({'userID': request.user.id, 'merge_name': '合并数据', 'fileData': merge_data})

                            try:
                                if db.find_one({'userID': request.user.id, 'un_merge_name': '初始合并数据'}):
                                    db.update({'userID': request.user.id, 'un_merge_name': '初始合并数据'},
                                              {'$set': {'un_data': merge_data}})
                                else:
                                    db.insert(
                                        {'userID': request.user.id, 'un_merge_name': '初始合并数据', 'un_data': merge_data})
                            except:
                                pass

                            if len(result) % 10 == 0:
                                amount = (len(result) / 10)
                            else:
                                amount = (len(result) // 10) + 1
                            if amount < 1:
                                result_data = result[0:].values.tolist()
                            elif num == 1:
                                result_data = result[0:11].values.tolist()
                            else:
                                result_data = result[(num * 10 - 9):(num * 10 + 1)].values.tolist()
                            new_data = json_util.loads(json_util.dumps(result_data))
                            for i in range(len(new_data)):
                                new_data[i] = list(map(str, new_data[i]))
                            return_json = {'status': True,
                                           'data': new_data,
                                           'amount': amount,
                                           'msg': '获取合并数据成功',
                                           }
                            logger.info(
                                "文件{0}，{1},{2},{3}的数据合并读取成功".format(click_file, click_file2, click_file3, click_file4))
                            return HttpResponse(json.dumps(return_json), content_type='application/json')
                        except Exception as e:

                            return_json = {'status': True,
                                           'data': [],
                                           'amount': None,
                                           'msg': '获取合并数据成功'}
                            logger.info(
                                "文件{0}，{1},{2},{3}的数据合并读取成功".format(click_file, click_file2, click_file3, click_file4))
                            return HttpResponse(json.dumps(return_json), content_type='application/json')
                    else:
                        return_json = {'status': True,
                                       'data': None,
                                       'amount': None,
                                       'msg': '获取表头成功',
                                       }
                        logger.error(
                            "文件{0}，{1},{2},{3}的数据合并读取失败：参数不够".format(click_file, click_file2, click_file3, click_file4))
                        return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '失败'}
                    logger.error(
                        "文件{0}，{1},{2},{3}的数据合并读取失败：{4}".format(click_file, click_file2, click_file3, click_file4, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')


            else:
                result = db.find({'_id': ObjectId(obj_id1)})
                try:
                    if re.search("\.(\w+)$", str((DataSource.objects.filter(id=int(click_file)).all())[
                                                     0].file_name)).group() in ['.txt', '.csv', '.CSV', '.TXT', '.sql']:
                        empty = pd.DataFrame()
                        data = empty.append(result[0]['fileData'])
                    if len(data) % 10 == 0:
                        amount = (len(data) / 10)
                    else:
                        amount = (len(data) // 10) + 1
                    if amount < 1:
                        result_data = data[0:].values.tolist()
                    elif num == 1:
                        result_data = data[0:11].values.tolist()
                    else:
                        result_data = data[(num * 10 - 9):(num * 10 + 1)].values.tolist()
                    file_data = json_util.loads(json_util.dumps(result_data))
                    for i in range(len(file_data)):
                        file_data[i] = list(map(str, file_data[i]))
                    return_json = {'status': True,
                                   'data': file_data,
                                   'amount': amount,
                                   'msg': '获取成功',
                                   }
                    logger.info("文件{0}的数据读取成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': True, 'data': None, 'msg': '获取失败'}
                    logger.error("文件{0}的数据读取失败：{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')


# 数据处理
class DataProView(APIView):
    """

    数据处理

    参数没有传空

    {

        type:get,

        url:/dispose/datapro/,

        data:{type:操作方式,

              num:当前页码,

              old_content:编辑前内容,

              content:编辑后内容,

              index:纵坐标,

              index_x:横坐标,

              click_file:点击第一个文件的id,

              click_file2:点击第二个文件的id,

              obj_id1:文件id,

              全大写:upper,

              全小写：letter，

              首字母大写：f_upper，

              删除列：delete，

              前向填充：prevfill，

              后向填充：netxfill，

              去除缺失值：de_value，

              归类通缉：classify，

              归类编辑：text，

              自定义填充：diyfill。

              },

        dataType:JSON,

    }
    """

    def get(self, request):
        my_mode = request.GET.get('type', '')
        content = request.GET.get('content', '')
        coordinate = request.GET.get('index', '')
        coordinate_x = request.GET.get('index_x', '')
        click_file = request.GET.get('click_file', '')
        click_file2 = request.GET.get('click_file2', '')
        old_content = request.GET.get('old_content', '')
        num = request.GET.get('num', 1)
        my_type = request.GET.get('my_type', '')
        obj_id1 = (DataSource.objects.filter(id=int(click_file)).all())[0].obj_id

        result = db.find({'_id': ObjectId(obj_id1)})
        fileData = result[0]['fileData']

        old_file = fileData
        if (db.find_one({'userID': request.user.id, 'old_name': '原数据'})):
            db.update({'userID': request.user.id, 'old_name': '原数据'}, {'$set': {'old_data': old_file}})
        else:
            db.insert({'userID': request.user.id, 'old_name': '原数据', 'old_data': old_file})
        if click_file and click_file2:
            result = db.find({'userID': request.user.id, 'merge_name': '合并数据'})
            # result_list = result[0]['fileData']
            result_list = result[0]['fileData']
            # 全大写
            if my_mode == 'upper':
                try:
                    for i in range(len(result_list[1:])):
                        (result_list[1:])[i][int(coordinate)] = ((result_list[1:])[i][int(coordinate)]).upper()
                    # db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    db.update({'userID': request.user.id, 'merge_name': '合并数据'}, {'$set': {'fileData': result_list}})
                    num = int(request.GET.get('num', 1))
                    empty = pd.DataFrame()
                    data = empty.append(result[0]['fileData'])

                    if num == 1:
                        result_data = data[0:11].values.tolist()
                    else:
                        result_data = data[(num * 10 - 9):(num * 10 + 1)].values.tolist()
                    file_data = json_util.loads(json_util.dumps(result_data))
                    return_json = {'status': True, 'data': file_data, 'msg': '全大写成功'}
                    logger.info("文件{0}的数据全大写成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '该组数据不支持该操作，请检查数据类型'}
                    logger.error("文件{0}的数据全大写失败：{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 全小写
            elif my_mode == 'letter':
                try:
                    for i in range(len(result_list[1:])):
                        (result_list[1:])[i][int(coordinate)] = ((result_list[1:])[i][int(coordinate)]).lower()
                    db.update({'userID': request.user.id, 'merge_name': '合并数据'}, {'$set': {'fileData': result_list}})
                    num = int(request.GET.get('num', 1))
                    empty = pd.DataFrame()
                    data = empty.append(result[0]['fileData'])

                    if num == 1:
                        result_data = data[0:11].values.tolist()
                    else:
                        result_data = data[(num * 10 - 9):(num * 10 + 1)].values.tolist()
                    file_data = json_util.loads(json_util.dumps(result_data))
                    return_json = {'status': True, 'data': file_data, 'msg': '全小写成功'}
                    logger.info("文件{0}的数据全小写成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '该组数据不支持该操作，请检查数据类型'}
                    logger.error("文件{0}的数据全小写失败:{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 首字母大写
            elif my_mode == 'f_upper':
                try:
                    for i in range(len(result_list[1:])):
                        (result_list[1:])[i][int(coordinate)] = ((result_list[1:])[i][int(coordinate)]).capitalize()
                    # db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    db.update({'userID': request.user.id, 'merge_name': '合并数据'}, {'$set': {'fileData': result_list}})
                    num = int(request.GET.get('num', 1))
                    empty = pd.DataFrame()
                    data = empty.append(result[0]['fileData'])

                    if num == 1:
                        result_data = data[0:11].values.tolist()
                    else:
                        result_data = data[(num * 10 - 9):(num * 10 + 1)].values.tolist()
                    file_data = json_util.loads(json_util.dumps(result_data))
                    return_json = {'status': True, 'data': file_data, 'msg': '首字母大写成功'}
                    logger.info("文件{0}的数据首字母大写成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '该组数据不支持该操作，请检查数据类型'}
                    logger.error("文件{0}的数据首字母大写失败:{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 删除列
            elif my_mode == 'delete':
                try:
                    for i in range(len(result_list)):
                        del (result_list[i][int(coordinate)])
                    db.update({'userID': request.user.id, 'merge_name': '合并数据'}, {'$set': {'fileData': result_list}})

                    num = int(request.GET.get('num', 1))
                    empty = pd.DataFrame()
                    data = empty.append(result[0]['fileData'])
                    title = data[0:1].values.tolist()
                    if num == 1:
                        result_data = data[0:11].values.tolist()
                    else:
                        result_data = data[(num * 10 - 9):(num * 10 + 1)].values.tolist()
                    file_data = json_util.loads(json_util.dumps(result_data))
                    for i in range(len(file_data)):
                        file_data[i] = list(map(str, file_data[i]))
                    return_json = {'status': True, 'data': file_data, 'title': title, 'msg': '删除列成功'}
                    logger.info("文件{0}的数据删除列成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '删除列失败'}
                    logger.error("文件{0}的数据删除列失败:{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 自定义填充
            elif my_mode == 'diyfill':
                try:
                    for i in range(len(result_list)):
                        result_list[int(coordinate_x)][int(coordinate)] = content
                    # db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    db.update({'userID': request.user.id, 'merge_name': '合并数据'}, {'$set': {'fileData': result_list}})
                    return_json = {'status': True, 'data': None, 'msg': '自定义填充成功'}
                    logger.info("文件{0}的数据自定义填充成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '自定义填充失败'}
                    logger.error("文件{0}的数据自定义填充失败：{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 前向填充
            elif my_mode == 'prevfill':
                try:
                    result_data = result_list[1:]
                    raw_data = []
                    for i in range(len(result_data)):
                        raw_data.append(result_data[i][int(coordinate)])

                    item_index = []
                    for item in enumerate(raw_data):
                        if item[1] == '':
                            item_index.append(item[0])

                    for i_index in item_index:
                        raw_data[i_index] = None
                    final_data = []
                    y = pd.DataFrame({'key': raw_data})
                    y_data = y.fillna(method='ffill')
                    for i in y_data.key:
                        final_data.append(i)
                    for i in range(len(result_list[1:])):
                        (result_list[1:])[i][int(coordinate)] = final_data[i]
                    # db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    db.update({'userID': request.user.id, 'merge_name': '合并数据'}, {'$set': {'fileData': result_list}})
                    num = int(request.GET.get('num', 1))
                    empty = pd.DataFrame()
                    data = empty.append(result[0]['fileData'])

                    if num == 1:
                        result_data = data[0:11].values.tolist()
                    else:
                        result_data = data[(num * 10 - 9):(num * 10 + 1)].values.tolist()
                    file_data = json_util.loads(json_util.dumps(result_data))
                    return_json = {'status': True, 'data': file_data, 'msg': '前向填充成功'}
                    logger.info("文件{0}的数据前向填充成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '前向填充失败'}
                    logger.error("文件{0}的数据前向填充失败".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 后向填充
            elif my_mode == 'netxfill':
                try:
                    result_data = result_list[1:]
                    raw_data = []
                    for i in range(len(result_data)):
                        raw_data.append(result_data[i][int(coordinate)])

                    item_index = []
                    for item in enumerate(raw_data):
                        if item[1] == '':
                            item_index.append(item[0])

                    for i_index in item_index:
                        raw_data[i_index] = None
                    final_data = []
                    y = pd.DataFrame({'key': raw_data})
                    y_data = y.fillna(method='bfill')
                    for i in y_data.key:
                        final_data.append(i)
                    for i in range(len(result_list[1:])):
                        (result_list[1:])[i][int(coordinate)] = final_data[i]
                    # db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    db.update({'userID': request.user.id, 'merge_name': '合并数据'}, {'$set': {'fileData': result_list}})
                    num = int(request.GET.get('num', 1))
                    empty = pd.DataFrame()
                    data = empty.append(result[0]['fileData'])

                    if num == 1:
                        result_data = data[0:11].values.tolist()
                    else:
                        result_data = data[(num * 10 - 9):(num * 10 + 1)].values.tolist()
                    file_data = json_util.loads(json_util.dumps(result_data))
                    return_json = {'status': True, 'data': file_data, 'msg': '后向填充成功'}
                    logger.info("文件{0}的数据后向填充成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '先后填充失败'}
                    logger.error("文件{0}的数据后向填充失败：{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 去除缺失值
            elif my_mode == 'de_value':
                try:
                    result_data = result_list[1:]
                    raw_data = []
                    for i in range(len(result_data)):
                        raw_data.append(result_data[i][int(coordinate)])
                    item_index = []
                    for item in enumerate(raw_data):
                        if item[1] == '':
                            item_index.append(item[0] + 1)
                    for i_index in sorted(item_index, reverse=True):
                        del result_list[i_index]
                    # db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    db.update({'userID': request.user.id, 'merge_name': '合并数据'}, {'$set': {'fileData': result_list}})
                    num = int(request.GET.get('num', 1))
                    empty = pd.DataFrame()
                    data = empty.append(result[0]['fileData'])

                    if num == 1:
                        result_data = data[0:11].values.tolist()
                    else:
                        result_data = data[(num * 10 - 9):(num * 10 + 1)].values.tolist()
                    file_data = json_util.loads(json_util.dumps(result_data))
                    return_json = {'status': True, 'data': file_data, 'msg': '去除缺失值成功'}
                    logger.info("文件{0}的数据去除缺失值成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '去除缺失值失败'}
                    logger.error("文件{0}的数据去除缺失值失败：{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 删除某一行
            elif my_mode == 'de_hang':
                try:

                    del result_list[int(coordinate_x)]
                    # db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    db.update({'userID': request.user.id, 'merge_name': '合并数据'}, {'$set': {'fileData': result_list}})
                    return_json = {'status': True, 'data': None, 'msg': '删除行成功'}
                    logger.info("文件{0}的数据删除行成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '删除行失败'}
                    logger.error("文件{0}的数据删除行失败：{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 归类统计
            elif my_mode == 'classify':
                try:
                    new_list = []
                    for i in range(len(result_list[1:])):
                        new_list.append(result_list[1:][i][int(coordinate)])
                    new_list = list(map(str, new_list))
                    countent = Counter(new_list)
                    res = {}
                    for i in new_list:
                        res[i] = res.get(i, 0) + 1
                    return_json = {'status': True, 'data': countent, 'msg': '归类统计成功'}
                    logger.info("文件{0}的数据归类统计成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '归类统计失败'}
                    logger.error("文件{0}的数据归类统计失败".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 归类编辑
            elif my_mode == 'text':
                try:
                    for i in range(len(result_list[1:])):
                        result_list[1:][i] = list(map(str, result_list[1:][i]))
                    for i in range(len(result_list[1:])):
                        if str(result_list[1:][i][int(coordinate)]) == old_content:
                            result_list[1:][i][int(coordinate)] = content
                    # db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    db.update({'userID': request.user.id, 'merge_name': '合并数据'}, {'$set': {'fileData': result_list}})
                    return_json = {'status': True, 'data': result_list, 'msg': '归类编辑成功'}
                    logger.info("文件{0}的数据归类编辑成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '归类编辑失败'}
                    logger.error("文件{0}的数据归类编辑失败:{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 数值类型转换为str
            elif my_mode == 'str':
                try:
                    for i in range(len(result_list[1:])):
                        (result_list[1:])[i][int(coordinate)] = str((result_list[1:])[i][int(coordinate)])
                    # db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    db.update({'userID': request.user.id, 'merge_name': '合并数据'}, {'$set': {'fileData': result_list}})
                    return_json = {'status': True, 'data': None, 'msg': '转字符串类型成功'}
                    logger.info("文件{0}的数据转换str成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '该组数据不支持该操作，请检查数据类型'}
                    logger.error("文件{0}的数据转换str失败:{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 数值类型转换为int
            elif my_mode == 'int':
                try:
                    for i in range(len(result_list[1:])):
                        (result_list[1:])[i][int(coordinate)] = float((result_list[1:])[i][int(coordinate)])
                    # db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    db.update({'userID': request.user.id, 'merge_name': '合并数据'}, {'$set': {'fileData': result_list}})
                    return_json = {'status': True, 'data': None, 'msg': '转数值型成功'}
                    logger.info("文件{0}的数据转换int成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '该组数据不支持该操作，请检查数据类型'}
                    logger.error("文件{0}的数据转换int失败:{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 函数计算
            elif my_mode == '函数计算':
                try:
                    my_list = []
                    for i in range(len(result_list[1:])):
                        my_list.append((result_list[1:])[i][int(coordinate)])
                    if my_type == '和':
                        data = Stats(my_list).sum()
                    elif my_type == '最大值':
                        data = Stats(my_list).max()
                    elif my_type == '最小值':
                        data = Stats(my_list).min()
                    elif my_type == '总个数':
                        data = Stats(my_list).count()
                    elif my_type == '平均值':
                        data = Stats(my_list).avg()
                    elif my_type == '中值':
                        data = Stats(my_list).median()
                    elif my_type == '标准差':
                        data = Stats(my_list).stdev()
                    return_json = {'status': True, 'data': data, 'msg': '函数计算成功'}
                    logger.info("文件{0}的数据计算成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': True, 'data': None, 'msg': '函数计算失败'}
                    logger.error("文件{0}的数计算失败:{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            else:
                return_json = {'status': False, 'data': None, 'msg': '没有该操作方式'}
                logger.error("没有该操作方式")
                return HttpResponse(json.dumps(return_json), content_type='application/json')
        else:
            result_list = result[0]['fileData']
            # 全大写
            if my_mode == 'upper':
                try:
                    for i in range(len(result_list[1:])):
                        (result_list[1:])[i][int(coordinate)] = ((result_list[1:])[i][int(coordinate)]).upper()
                    db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    num = int(request.GET.get('num', 1))
                    empty = pd.DataFrame()
                    data = empty.append(result[0]['fileData'])

                    if num == 1:
                        result_data = data[0:11].values.tolist()
                    else:
                        result_data = data[(num * 10 - 9):(num * 10 + 1)].values.tolist()
                    file_data = json_util.loads(json_util.dumps(result_data))
                    return_json = {'status': True, 'data': file_data, 'msg': '全大写成功'}
                    logger.info("文件{0}的数据全大写成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '该组数据不支持该操作，请检查数据类型'}
                    logger.error("文件{0}的数据全大写失败：{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 全小写
            elif my_mode == 'letter':
                try:
                    for i in range(len(result_list[1:])):
                        (result_list[1:])[i][int(coordinate)] = ((result_list[1:])[i][int(coordinate)]).lower()
                    db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    num = int(request.GET.get('num', 1))
                    empty = pd.DataFrame()
                    data = empty.append(result[0]['fileData'])

                    if num == 1:
                        result_data = data[0:11].values.tolist()
                    else:
                        result_data = data[(num * 10 - 9):(num * 10 + 1)].values.tolist()
                    file_data = json_util.loads(json_util.dumps(result_data))
                    return_json = {'status': True, 'data': file_data, 'msg': '全小写成功'}
                    logger.info("文件{0}的数据全小写成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '该组数据不支持该操作，请检查数据类型'}
                    logger.error("文件{0}的数据全小写失败:{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 首字母大写
            elif my_mode == 'f_upper':
                try:
                    for i in range(len(result_list[1:])):
                        (result_list[1:])[i][int(coordinate)] = ((result_list[1:])[i][int(coordinate)]).capitalize()
                    db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    num = int(request.GET.get('num', 1))
                    empty = pd.DataFrame()
                    data = empty.append(result[0]['fileData'])

                    if num == 1:
                        result_data = data[0:11].values.tolist()
                    else:
                        result_data = data[(num * 10 - 9):(num * 10 + 1)].values.tolist()
                    file_data = json_util.loads(json_util.dumps(result_data))
                    return_json = {'status': True, 'data': file_data, 'msg': '首字母大写成功'}
                    logger.info("文件{0}的数据首字母大写成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '该组数据不支持该操作，请检查数据类型'}
                    logger.error("文件{0}的数据首字母大写失败:{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 删除列
            elif my_mode == 'delete':
                try:
                    for i in range(len(result_list)):
                        del (result_list[i][int(coordinate)])
                    db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})

                    num = int(request.GET.get('num', 1))
                    empty = pd.DataFrame()
                    data = empty.append(result[0]['fileData'])
                    title = data[0:1].values.tolist()
                    if num == 1:
                        result_data = data[0:11].values.tolist()
                    else:
                        result_data = data[(num * 10 - 9):(num * 10 + 1)].values.tolist()
                    file_data = json_util.loads(json_util.dumps(result_data))
                    for i in range(len(file_data)):
                        file_data[i] = list(map(str, file_data[i]))
                    return_json = {'status': True, 'data': file_data, 'title': title, 'msg': '删除列成功'}
                    logger.info("文件{0}的数据删除列成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '删除列失败'}
                    logger.error("文件{0}的数据删除列失败:{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 自定义填充
            elif my_mode == 'diyfill':
                try:
                    for i in range(len(result_list)):
                        result_list[int(coordinate_x)][int(coordinate)] = content
                    db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    return_json = {'status': True, 'data': None, 'msg': '自定义填充成功'}
                    logger.info("文件{0}的数据自定义填充成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:
                    return_json = {'status': False, 'data': None, 'msg': '自定义填充失败'}
                    logger.error("文件{0}的数据自定义填充失败：{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 前向填充
            elif my_mode == 'prevfill':
                try:
                    result_data = result_list[1:]
                    raw_data = []
                    for i in range(len(result_data)):
                        raw_data.append(result_data[i][int(coordinate)])

                    item_index = []
                    for item in enumerate(raw_data):
                        if item[1] == '':
                            item_index.append(item[0])

                    for i_index in item_index:
                        raw_data[i_index] = None
                    final_data = []
                    y = pd.DataFrame({'key': raw_data})
                    y_data = y.fillna(method='ffill')
                    for i in y_data.key:
                        final_data.append(i)
                    for i in range(len(result_list[1:])):
                        (result_list[1:])[i][int(coordinate)] = final_data[i]
                    db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    num = int(request.GET.get('num', 1))
                    empty = pd.DataFrame()
                    data = empty.append(result[0]['fileData'])

                    if num == 1:
                        result_data = data[0:11].values.tolist()
                    else:
                        result_data = data[(num * 10 - 9):(num * 10 + 1)].values.tolist()
                    file_data = json_util.loads(json_util.dumps(result_data))
                    return_json = {'status': True, 'data': file_data, 'msg': '前向填充成功'}
                    logger.info("文件{0}的数据前向填充成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '前向填充失败'}
                    logger.error("文件{0}的数据前向填充失败".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 后向填充
            elif my_mode == 'netxfill':
                try:
                    result_data = result_list[1:]
                    raw_data = []
                    for i in range(len(result_data)):
                        raw_data.append(result_data[i][int(coordinate)])

                    item_index = []
                    for item in enumerate(raw_data):
                        if item[1] == '':
                            item_index.append(item[0])

                    for i_index in item_index:
                        raw_data[i_index] = None
                    final_data = []
                    y = pd.DataFrame({'key': raw_data})
                    y_data = y.fillna(method='bfill')
                    for i in y_data.key:
                        final_data.append(i)
                    for i in range(len(result_list[1:])):
                        (result_list[1:])[i][int(coordinate)] = final_data[i]
                    db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    num = int(request.GET.get('num', 1))
                    empty = pd.DataFrame()
                    data = empty.append(result[0]['fileData'])

                    if num == 1:
                        result_data = data[0:11].values.tolist()
                    else:
                        result_data = data[(num * 10 - 9):(num * 10 + 1)].values.tolist()
                    file_data = json_util.loads(json_util.dumps(result_data))
                    return_json = {'status': True, 'data': file_data, 'msg': '后向填充成功'}
                    logger.info("文件{0}的数据后向填充成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '先后填充失败'}
                    logger.error("文件{0}的数据后向填充失败：{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 去除缺失值
            elif my_mode == 'de_value':
                try:
                    result_data = result_list[1:]
                    raw_data = []
                    for i in range(len(result_data)):
                        raw_data.append(result_data[i][int(coordinate)])
                    item_index = []
                    for item in enumerate(raw_data):
                        if item[1] == '':
                            item_index.append(item[0] + 1)
                    for i_index in sorted(item_index, reverse=True):
                        del result_list[i_index]
                    db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    num = int(request.GET.get('num', 1))
                    empty = pd.DataFrame()
                    data = empty.append(result[0]['fileData'])

                    if num == 1:
                        result_data = data[0:11].values.tolist()
                    else:
                        result_data = data[(num * 10 - 9):(num * 10 + 1)].values.tolist()
                    file_data = json_util.loads(json_util.dumps(result_data))
                    return_json = {'status': True, 'data': file_data, 'msg': '去除缺失值成功'}
                    logger.info("文件{0}的数据去除缺失值成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '去除缺失值失败'}
                    logger.error("文件{0}的数据去除缺失值失败：{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 删除某一行
            elif my_mode == 'de_hang':
                try:

                    del result_list[int(coordinate_x)]
                    db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    return_json = {'status': True, 'data': None, 'msg': '删除行成功'}
                    logger.info("文件{0}的数据删除行成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '删除行失败'}
                    logger.error("文件{0}的数据删除行失败：{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 归类统计
            elif my_mode == 'classify':
                try:
                    new_list = []
                    for i in range(len(result_list[1:])):
                        new_list.append(result_list[1:][i][int(coordinate)])
                    new_list = list(map(str, new_list))
                    countent = Counter(new_list)
                    res = {}
                    for i in new_list:
                        res[i] = res.get(i, 0) + 1
                    return_json = {'status': True, 'data': countent, 'msg': '归类统计成功'}
                    logger.info("文件{0}的数据归类统计成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '归类统计失败'}
                    logger.error("文件{0}的数据归类统计失败".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 归类编辑
            elif my_mode == 'text':
                try:
                    for i in range(len(result_list[1:])):
                        result_list[1:][i] = list(map(str, result_list[1:][i]))
                    for i in range(len(result_list[1:])):
                        if str(result_list[1:][i][int(coordinate)]) == old_content:
                            result_list[1:][i][int(coordinate)] = content
                    db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    return_json = {'status': True, 'data': result_list, 'msg': '归类编辑成功'}
                    logger.info("文件{0}的数据归类编辑成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '归类编辑失败'}
                    logger.error("文件{0}的数据归类编辑失败:{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 数值类型转换为str
            elif my_mode == 'str':
                try:
                    for i in range(len(result_list[1:])):
                        (result_list[1:])[i][int(coordinate)] = str((result_list[1:])[i][int(coordinate)])
                    db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    return_json = {'status': True, 'data': None, 'msg': '转字符串类型成功'}
                    logger.info("文件{0}的数据转换str成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:

                    return_json = {'status': False, 'data': None, 'msg': '该组数据不支持该操作，请检查数据类型'}
                    logger.error("文件{0}的数据转换str失败:{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 数值类型转换为int
            elif my_mode == 'int':
                try:
                    for i in range(len(result_list[1:])):
                        (result_list[1:])[i][int(coordinate)] = float((result_list[1:])[i][int(coordinate)])
                    db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result_list}})
                    return_json = {'status': True, 'data': None, 'msg': '转数值型成功'}
                    logger.info("文件{0}的数据转换int成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:
                    return_json = {'status': False, 'data': None, 'msg': '该组数据不支持该操作，请检查数据类型'}
                    logger.error("文件{0}的数据转换int失败:{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            # 函数计算
            elif my_mode == '函数计算':
                try:
                    my_list = []
                    for i in range(len(result_list[1:])):
                        my_list.append((result_list[1:])[i][int(coordinate)])
                    if my_type == '和':
                        data = Stats(my_list).sum()
                    elif my_type == '最大值':
                        data = Stats(my_list).max()
                    elif my_type == '最小值':
                        data = Stats(my_list).min()
                    elif my_type == '总个数':
                        data = Stats(my_list).count()
                    elif my_type == '平均值':
                        data = Stats(my_list).avg()
                    elif my_type == '中值':
                        data = Stats(my_list).median()
                    elif my_type == '标准差':
                        data = Stats(my_list).stdev()
                    return_json = {'status': True, 'data': data, 'msg': '函数计算成功'}
                    logger.info("文件{0}的数据计算成功".format(click_file))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
                except Exception as e:
                    return_json = {'status': True, 'data': None, 'msg': '函数计算失败'}
                    logger.error("文件{0}的数计算失败:{1}".format(click_file, e))
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

            else:
                return_json = {'status': False, 'data': None, 'msg': '没有该操作方式'}
                logger.error("没有该操作方式")
                return HttpResponse(json.dumps(return_json), content_type='application/json')


# 撤销
class CancelView(APIView):
    """
    撤销

    参数没有传空

    {

        type:get,

        url:/dispose/cancel/,

        data:{search:搜索的关键词,

              click_file:第一个文件的id,

              click_file2:第二个文件的id,

            },

        dataType:JSON,
    }
    """

    def get(self, request):
        click_file = request.GET.get('click_file', '')
        click_file2 = request.GET.get('click_file2', '')
        result = db.find({'userID': request.user.id, 'old_name': '原数据'})[0]['old_data']
        result2 = db.find({'userID': request.user.id, 'un_merge_name': '初始合并数据'})[0]['un_data']
        if click_file and click_file2:
            db.update({'userID': request.user.id, 'merge_name': '合并数据'}, {'$set': {'fileData': result2}})
            data = db.find({'userID': request.user.id, 'merge_name': '合并数据'})[0]['fileData']
            empty = pd.DataFrame()
            data = empty.append(data)
            if len(data) % 10 == 0:
                amount = (len(data) / 10)
            else:
                amount = (len(data) // 10) + 1

            if amount < 1:
                result_data = data[0:].values.tolist()

            else:
                result_data = data[0:11].values.tolist()
            file_data = json_util.loads(json_util.dumps(result_data))
            for i in range(len(file_data)):
                file_data[i] = list(map(str, file_data[i]))
            return_json = {'status': True,
                           'data': file_data,
                           'amount': amount,
                           'msg': '获取成功',
                           }
            logger.info("文件撤销成功".format(click_file))
            return HttpResponse(json.dumps(return_json), content_type='application/json')
        else:
            obj_id1 = (DataSource.objects.filter(id=int(click_file)).all())[0].obj_id
            db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result}})

            data = db.find({'_id': ObjectId(obj_id1)})[0]['fileData']
            empty = pd.DataFrame()
            data = empty.append(data)
            if len(data) % 10 == 0:
                amount = (len(data) / 10)
            else:
                amount = (len(data) // 10) + 1

            if amount < 1:
                result_data = data[0:].values.tolist()

            else:
                result_data = data[0:11].values.tolist()
            file_data = json_util.loads(json_util.dumps(result_data))
            for i in range(len(file_data)):
                file_data[i] = list(map(str, file_data[i]))
            return_json = {'status': True,
                           'data': file_data,
                           'amount': amount,
                           'msg': '获取成功',
                           }
            logger.info("文件撤销成功".format(click_file))
            return HttpResponse(json.dumps(return_json), content_type='application/json')


# 取消回到初始状态
class UndoView(APIView):
    """
    取消回到初始状态

    参数没有传空

    {

        type:get,

        url:/dispose/undo/,

        data:{

              click_file:第一个文件的id,

              click_file2:第二个文件的id,

            },

        dataType:JSON,
    }
    """

    def get(self, request):
        click_file = request.GET.get('click_file')
        click_file2 = request.GET.get('click_file2')
        if click_file and click_file2:
            result = db.find({'userID': request.user.id, 'un_merge_name': '初始合并数据'})[0]['un_data']
            db.update({'userID': request.user.id, 'merge_name': '合并数据'}, {'$set': {'fileData': result}})
            data = db.find({'userID': request.user.id, 'merge_name': '合并数据'})[0]['fileData']
            empty = pd.DataFrame()
            data = empty.append(data)
            if len(data) % 10 == 0:
                amount = (len(data) / 10)
            else:
                amount = (len(data) // 10) + 1

            if amount < 1:
                result_data = data[0:].values.tolist()

            else:
                result_data = data[0:11].values.tolist()
            file_data = json_util.loads(json_util.dumps(result_data))
            for i in range(len(file_data)):
                file_data[i] = list(map(str, file_data[i]))
            return_json = {'status': True,
                           'data': file_data,
                           'amount': amount,
                           'msg': '获取成功',
                           }
            logger.info("文件取消操作成功".format(click_file))
            return HttpResponse(json.dumps(return_json), content_type='application/json')
        else:
            obj_id1 = (DataSource.objects.filter(id=int(click_file)))[0].obj_id
            result = db.find({'userID': request.user.id, 'un_name': '初始数据'})[0]['un_data']
            db.update({'_id': ObjectId(obj_id1)}, {'$set': {'fileData': result}})
            if re.search("\.(\w+)$", str((DataSource.objects.get(id=int(click_file))).file_name)).group() in ['.txt',
                                                                                                              '.csv',
                                                                                                              '.CSV',
                                                                                                              '.TXT',
                                                                                                              '.sql']:
                data = db.find({'_id': ObjectId(obj_id1)})[0]['fileData']
                empty = pd.DataFrame()
                data = empty.append(data)
                if len(data) % 10 == 0:
                    amount = (len(data) / 10)
                else:
                    amount = (len(data) // 10) + 1

                if amount < 1:
                    result_data = data[0:].values.tolist()

                else:
                    result_data = data[0:11].values.tolist()
                file_data = json_util.loads(json_util.dumps(result_data))
                for i in range(len(file_data)):
                    file_data[i] = list(map(str, file_data[i]))
                return_json = {'status': True,
                               'data': file_data,
                               'amount': amount,
                               'msg': '获取成功',
                               }
                logger.info("文件取消操作成功".format(click_file))
                return HttpResponse(json.dumps(return_json), content_type='application/json')


# 保存上传数据
class UpMergeView(APIView):
    """
    保存上传数据

    参数没有传空

    {

        type:get,

        url:/dispose/upsave/,

        data:{old_file：第一个文件id,

              old_file2：第二个文件id,

              old_file3：第三个文件id,

              old_file4：第四个文件id,

              new_file:新文件名称,

            },

        dataType:JSON,
    }
    """

    def get(self, request):
        old_file = request.GET.get('old_file', '')
        old_file2 = request.GET.get('old_file2', '')
        new_file = request.GET.get('new_file', '')

        if old_file and not old_file2:
            o_id = (DataSource.objects.filter(id=old_file))[0].obj_id
            data = db.find({'_id': ObjectId(o_id)})[0]['fileData']
            content = {
                'fileName': new_file + '.csv',
                'userID': request.user.id,
                'fileData': data
            }
            objectID = db.insert(content)
            objectID = string_type(objectID)
            item = DataSource()
            item.obj_id = objectID
            item.user_id = request.user.id
            item.file_name = new_file + '.csv'
            item.share_status = 1
            item.where = 'mongodb'
            item.save()
            result = db.find({'userID': request.user.id, 'un_name': '初始数据'})[0]['un_data']
            db.update({'_id': ObjectId(o_id)}, {'$set': {'fileData': result}})
            return_json = {'status': True, 'data': str(objectID), 'msg': '保存成功'}
            logger.info("文件保存成功")
            return HttpResponse(json.dumps(return_json), content_type='application/json')

        elif old_file and old_file2:
            data = db.find({'userID': request.user.id, 'merge_name': '合并数据'})[0]['fileData']
            content = {
                'fileName': new_file + '.csv',
                'userID': request.user.id,
                'fileData': data
            }
            db.insert(content)
            objectID = db.find({'userID': request.user.id, 'fileName': new_file + '.csv'})[0]['_id']
            item = DataSource()
            item.obj_id = objectID
            item.user_id = request.user.id
            item.file_name = new_file + '.csv'
            item.where = 'mongodb'
            item.save()
            return_json = {'status': True, 'data': str(objectID), 'msg': '保存成功'}
            logger.info("保存成功")
            return HttpResponse(json.dumps(return_json), content_type='application/json')


# 修改文件名
class UpNameView(APIView):
    """
    修改文件名

    参数没有传空

    {

        type:get,

        url:/dispose/upname/,

        data:{o_filename：旧的文件id,

              n_filename：新的文件名,

            },

        dataType:JSON,
    }
    """

    def get(self, request):
        try:
            o_filename = request.GET.get('o_filename', '')
            n_filename = request.GET.get('n_filename', '')
            thumb = DataSource.objects.filter(id=o_filename)[0]
            old_name = thumb.file_name
            houzhui = re.search("\.(\w+)$", str(old_name)).group()
            if re.search("\.(\w+)$", (str(n_filename) + houzhui)).group() in ['.txt', '.csv', '.sql']:
                DataSource.objects.filter(id=o_filename).update(file_name=n_filename + houzhui)
                return_json = {'status': True, 'data': n_filename + houzhui, 'msg': '修改成功'}
                logger.info("修改文件名成功".format(o_filename))
                return HttpResponse(json.dumps(return_json), content_type='application/json')
            else:
                return_json = {'status': True, 'data': None, 'msg': '修改失败，请检查文件名是否符合规范！'}
                logger.error("修改文件名失败，请检查文件名是否符合规范！".format(o_filename))
                return HttpResponse(json.dumps(return_json), content_type='application/json')
        except:
            return_json = {'status': True, 'data': None, 'msg': '修改失败，请检查文件名是否符合规范！'}
            logger.error("修改文件名失败，请检查文件名是否符合规范！".format(o_filename))
            return HttpResponse(json.dumps(return_json), content_type='application/json')


# 调用算法
class FunView(APIView):
    """
    调用算法

    参数没有传空

    {

        type:get,

        url:/dispose/fun/,

        data:{

              待定,

            },

        dataType:JSON,
    }
    """

    def get(self, request):
        user_id = request.user.id
        arg_list = request.GET.get("cn_list")
        defApp = request.GET.get("defApp", "")
        arg_list = json.loads(arg_list)
        result = []
        try:
            rel = getattr(tasks, defApp, 'no exit').delay(*arg_list)
            while True:
                if rel.ready():
                    rel = rel.result
                    result.append(rel)

                    break
            try:
                result = json.loads(result[0])
            except Exception as e:
                return_json = {'status': False, 'data': None, 'msg': '数据格式不正确，请采用正确的数据格式'}
                return HttpResponse(json.dumps(return_json), content_type='application/json')
            if result['status'] == True:
                if defApp == 'PCA_func':
                    item = db.find({'_id': ObjectId(result['data'])})[0]
                    data = item['fileData']
                    thumb = item['result']
                    info = {'MODEL_VERIFICATION': thumb['MODEL_VERIFICATION'],
                            'MODEL_VERIFICATION_2': thumb['MODEL_VERIFICATION_2'],
                            'PREDICTED_RESULTS_ON_TRAINING_DATA': thumb['PREDICTED_RESULTS_ON_TRAINING_DATA'],
                            }
                    return_json = {'status': True, 'data': data, 'result': info, 'obj_id': result['data'], 'msg': '成功'}
                    return HttpResponse(json.dumps(return_json), content_type='application/json')

                elif defApp == 'FactorAnalysis':
                    item = db.find({'_id': ObjectId(result['data'])})[0]
                    data = item['fileData']
                    thumb = item['result']
                    info = {'DRAW_DATA': thumb['DRAW_DATA'],
                            'result_data': thumb['result_data'],
                            'result_validation_1': thumb['result_validation_1'],
                            'result_validation_2': thumb['result_validation_2'],
                            'result_validation_3': thumb['result_validation_3'],
                            }
                    try:
                        return_json = {'status': True, 'data': data, 'result': info, 'obj_id': result['data'],
                                       'msg': '成功'}
                        return HttpResponse(json.dumps(return_json), content_type='application/json')
                    except Exception as e:

                        return_json = {'status': False, 'data': None, 'msg': '数据错误'}
                        return HttpResponse(json.dumps(return_json), content_type='application/json')

                elif defApp == 'OutliersProcessing_func':
                    item = db.find({'_id': ObjectId(result['data'])})[0]
                    data = item['fileData']
                    thumb = item['result']
                    info = {'MODEL_VERIFICATION': thumb['MODEL_VERIFICATION'],
                            'PREDICTED_RESULTS_ON_TRAINING_DATA': thumb['PREDICTED_RESULTS_ON_TRAINING_DATA'],
                            }
                    try:
                        return_json = {'status': True, 'data': data, 'result': info, 'obj_id': result['data'],
                                       'msg': '成功'}
                        return HttpResponse(json.dumps(return_json), content_type='application/json')
                    except Exception as e:

                        return_json = {'status': False, 'data': None, 'msg': '数据错误'}
                        return HttpResponse(json.dumps(return_json), content_type='application/json')

                else:
                    data = db.find({'_id': ObjectId(result['data'])})[0]['fileData']
                    return_json = {'status': True, 'data': data, 'obj_id': result['data'], 'msg': '成功'}
                    return HttpResponse(json.dumps(return_json), content_type='application/json')
            else:
                data = result['error']
                return_json = {'status': False, 'data': None, 'msg': data}
                return HttpResponse(json.dumps(return_json), content_type='application/json')
        except Exception as e:
            return_json = {'status': False, 'data': None, 'msg': e}
            return HttpResponse(json.dumps(return_json), content_type='application/json')


# 下一步
class NextView(APIView):
    """
    下一步

    参数没有传空

    {

        type:get,

        url:/dispose/next/,

        data:{click_file：点击的文件id,

            },

        dataType:JSON,
    }
    """

    def get(self, request):
        obj_id = request.GET.get('obj_id', '')
        click_file = request.GET.get('click_file', '')
        if obj_id:
            object_id = obj_id
        else:
            user_id = request.user.id
            object_id = (DataSource.objects.filter(user=user_id, id=int(click_file)))[0].obj_id
        return_json = {'status': True, 'data': object_id, 'msg': '成功'}
        logger.info("文件：{0}已成功进入下一步".format(click_file))
        return HttpResponse(json.dumps(return_json), content_type='application/json')


# 删除文件
class DelView(APIView):
    """
    删除文件

    参数没有传空

    {

        type:get,

        url:/dispose/del/,

        data:{file：点击的文件id,

            },

        dataType:JSON,
    }
    """

    def get(self, request):
        file = int(request.GET.get('file', 1))
        try:
            DataSource.objects.filter(id=file).delete()
            item = Collect.objects.filter(file_id=file)
            if item:
                item.delete()
            return_json = {'status': True, 'data': None, 'msg': '删除成功'}
            logger.info("文件：{0}删除成功".format(file))
            return HttpResponse(json.dumps(return_json), content_type='application/json')
        except Exception as e:
            return_json = {'status': False, 'data': None, 'msg': '删除失败'}
            logger.error("文件：{0}删除失败:{1}".format(file, e))
            return HttpResponse(json.dumps(return_json), content_type='application/json')


# 算法请求表头
class LieView(APIView):
    """
    算法请求表头

    参数没有传空

    {

        type:get,

        url:/dispose/title/,

        data:{filename：点击的文件id,

            },

        dataType:JSON,
    }
    """

    def get(self, request):
        filename = request.GET.get('filename', '')
        obj_id = DataSource.objects.get(id=filename).obj_id
        file_mongo_id = (DataSource.objects.filter(id=filename).all())[0].obj_id
        if filename or obj_id:
            if obj_id:
                thumb = db.find({'_id': ObjectId(obj_id)})[0]['fileName']
                item = db.find({'_id': ObjectId(obj_id)})[0]['fileData'][0]
                return_json = ({'status': True, 'data': item, 'obj_id': obj_id, 'msg': '成功'})
                logger.info("文件：{0}表头请求成功".format(filename))
                return HttpResponse(json.dumps(return_json), content_type='application/json')

            else:

                item = db.find({'_id': ObjectId(file_mongo_id)})[0]['fileData'][0]
                id = string_type(db.find({'_id': ObjectId(file_mongo_id)})[0]['_id'])
                return_json = ({'status': True, 'data': item, 'obj_id': id, 'msg': '成功'})
                logger.info("文件：{0}表头请求成功".format(filename))
                return HttpResponse(json.dumps(return_json), content_type='application/json')

        else:
            return_json = ({'status': False, 'data': None, 'msg': '请选择文件'})
            logger.info("没有选择文件")
            return HttpResponse(json.dumps(return_json), content_type='application/json')


# 保存算法数据
class SaveView(APIView):
    """
    保存算法数据

    参数没有传空

    {

        type:get,

        url:/dispose/savealg/,

        data:{filename:用户 设置/输入 的文件名,

              file_id:文件id,

            },

        dataType:JSON,
    }
    """

    def get(self, request):
        file_id = request.GET.get('file_id', '')
        obj_id = DataSource.objects.get(id=file_id).obj_id
        filename = request.GET.get('filename', '')
        user_id = request.user.id

        data = db.find({'_id': ObjectId(obj_id)})[0]['fileData']
        content = {'userID': user_id,
                   'fileData': data,
                   'fileName': filename + '.csv',
                   }
        objectID = db.insert(content)
        objectID = string_type(objectID)

        dataframe = pd.DataFrame(data)
        row = dataframe.columns.size
        col = dataframe.iloc[:, 0].size
        title = data[0]

        num = '%.2f' % (len(str(content)) / 1024)
        item = DataSource()
        item.file_name = filename + '.csv'
        item.obj_id = objectID
        item.user = user_id
        item.fileSize = num + 'KB'
        item.row_num = row
        item.column_num = col
        item.title = title
        item.save()
        return_json = {'status': True, 'data': str(objectID), 'msg': '保存成功'}
        logger.info("算法数据保存成功")
        return HttpResponse(json.dumps(return_json), content_type='application/json')


@api_view(['GET'])
def Download(request):
    """
    请求路由: dispose/download;

    请求方式：get;

    参数：click_file（文件id）;

    数据文件下载<br>
    :param request:
    :param site_name:文件名
    :param jira_version:版本号
    :return:
    """
    objID = DataSource.objects.get(id=int(request.GET.get('click_file'))).obj_id

    datas = db.find_one({"_id": ObjectId(objID)})["fileData"]
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
