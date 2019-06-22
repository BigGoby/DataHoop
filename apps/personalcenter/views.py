import datetime
import hashlib
import json
import random
import string
import os
import time
import pymongo

from rest_framework import mixins, viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from Datahoop.settings import HDFS_HOST
from hdfs import Client
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from PIL import Image
from bson import ObjectId
from django.conf import settings
from django.core import serializers
from django.http import JsonResponse
from django.shortcuts import HttpResponse
from .models import MyCourse, OperationSettings
from .serializers import MyCourseSerializer, AlgGetSerializer
from algorithm.models import Algorithms, ModelResult
from files.models import DataSource
from files.models import UserProfile, AlgoLabel, Model_Label, DataSourcelLabel, StorageLabel
from users.models import UserLevel
from personalcenter import tests
from personalcenter.models import MyNote, Collect
from personalcenter.models import Myscore
from personalcenter.models import Relationship
from personalcenter.models import Sign
from share.models import SharingCollect
from share.models import SharingFile
from django.db.models import Q
from .models import UserFellBack

client = pymongo.MongoClient(settings.MONGO_DB_URI)
db = client.datahoop.data


class Mydata(APIView):
    def get(self, request):
        id = request.user.id
        page = request.GET.get('page')
        page = int(page)
        myData = DataSource.objects.filter(Q(user_id=id) & ~Q(obj_id=''))
        sum = myData.count()
        myData = myData[::-1]
        my_data_list = myData[page * 13 - 13:page * 13]
        #  查找用户上传的文件所使用的大小
        myData_size = 0
        for i in myData:
            try:
                x = i.fileSize.replace("KB", '')
                myData_size += float(x)
            except:
                continue
        myData_size = round(myData_size / 1024, 2)  # 单位MB
        if myData:
            c = []
            myData = serializers.serialize('json', my_data_list)
            for i in json.loads(myData):
                data = {}
                data['name'] = i['fields']['file_name']
                data['sum'] = sum
                data['id'] = i['pk']
                data['type'] = i['fields']['file_name'].rsplit('.', 1)[-1]
                data['share_status'] = i['fields']['share_status']
                c.append(data)
            data_size = {'mydata': str(myData_size) + 'MB'}
            mydata_size = {'myBigData': str(myData_size) + 'MB'}
            return HttpResponse(
                json.dumps({'status': True, 'json': c, 'data_size': data_size, 'max_size': mydata_size}),
                content_type='application/json')
        else:
            return HttpResponse(json.dumps({'status': False, }))


class Data_share(APIView):
    def get(self, request):  # share_mydata
        try:
            user = request.user.id
            id = request.GET.get('file_id')
            type = request.GET.get('name')
            price = request.GET.get('price')
            desc = request.GET.get('desc')
            label = request.GET.get('label')
            # myData = serializers.serialize('json', DataSource.objects.filter(id=id))
            # share_status=0 0代表共享
            #  1, "商业"),(2, "文化"),(3, "环境"),(4, "生活"),(5, "社会"),(6, "体育"),(7, "教育"),(8, "科技"),9, "时政")
            DataSource.objects.filter(pk=id).update(price=price, detail=desc, parent=label, label_name=type,
                                                    category=1, share_status=0)
            # obj = DataSourcelLabel.objects.filter(id=label).update(name=type,parent=label )
            return JsonResponse({'status': True, 'msg': '共享成功'})
        except Exception as e:
            print(e)
            return JsonResponse({'status': False, 'msg': '共享失败'})


def note_share(request):  # share_mynote
    permission_classes = (IsAuthenticated,)
    try:
        if request.method == 'GET':
            user = request.user.id
            source = request.user.phone
            id = request.GET.get('noteid')
            type = request.GET.get('checkhy')
            price = request.GET.get('price')
            desc = request.GET.get('desc')
            label = request.GET.get('label')
            MyNote.objects.filter(pk=id).update(
                share_status=0)
            myData = serializers.serialize('json', MyNote.objects.filter(id=id))
            for i in json.loads(myData):
                obj = SharingFile(score=price, desc=desc, label=label, title=i['fields']['title'],
                                  content=i['fields']['content'], user_id=user, category=1, source=source, tag=type)
                obj.save()
            return JsonResponse({'status': True, 'msg': '共享成功'})
    except Exception as e:
        return JsonResponse({'status': False, 'msg': '共享失败'})


def delete_note(request):  # delete mynote
    msg = {}
    if request.method == 'GET':
        id = request.GET.get('id')
        file_id = MyNote.objects.filter(id=id)
        file_id.delete()
        msg['status'] = True
        return JsonResponse(msg)


import pymongo


# client = pymongo.MongoClient(settings.MONGO_DB_URI)
# db = client.datahoop.data


class Delete_data(APIView):
    def get(self, request):  # delete mydata
        file_id = request.GET.get('file_id')
        try:
            where = DataSource.objects.get(id=file_id).where
            print(DataSource.objects.get(id=file_id))
            print(where)
            format_filename = DataSource.objects.get(id=file_id).format_filename
            format_name_count = DataSource.objects.filter(format_filename=format_filename).count()
            if where == 'hdfs' and format_name_count == 1:
                file = DataSource.objects.get(id=file_id)
                hdfs_name = DataSource.objects.get(id=file_id).format_filename
                client = Client(HDFS_HOST)
                client.delete('/datahoop/' + hdfs_name, recursive=True)
                file.delete()
                item = Collect.objects.filter(file_id=file_id)
                if item:
                    item.delete()
            elif where == 'hdfs' and format_name_count > 1:
                file = DataSource.objects.get(id=file_id)
                file.delete()
                item = Collect.objects.filter(file_id=file_id)
                if item:
                    item.delete()
            else:
                client = pymongo.MongoClient(settings.MONGO_DB_URI)
                db = client.datahoop.data
                data_obj = DataSource.objects.filter(id=file_id).first()
                obj_id = data_obj.obj_id
                data_obj.delete()
                db.remove({"_id": ObjectId(obj_id)})
                client.close()
                item = Collect.objects.filter(file_id=file_id)
                if item:
                    item.delete()
            return JsonResponse({'status': True})
        except:
            return JsonResponse({'status': False})


def delete_model(request):  # delete mymodel

    client = pymongo.MongoClient(settings.MONGO_DB_URI)
    db = client.mark.models
    msg = {}
    if request.method == 'GET':
        id = request.GET.get('id')
        file_id = ModelResult.objects.filter(id=id)
        obj_id = file_id[0].OBJID
        file_id.delete()
        item = Collect.objects.filter(file_id=id)
        if item:
            item.delete()
        db.remove({"_id": ObjectId(obj_id)})

        msg['status'] = True
        db.close()
        return JsonResponse(msg)


class Userprofile(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        id = request.user.id
        # id = UserProfile.objects.filter(phone=username)[0].id
        myData = serializers.serialize('json', UserProfile.objects.filter(id=id))
        print(json.loads(myData))
        data = {}
        for i in json.loads(myData):
            data['name'] = i['fields']['name']
            data['username'] = i['fields']['username']
            data['phone'] = i['fields']['mobile']
            data['date'] = i['fields']['date_joined'].split('T')[0]
            data['first_name'] = i['fields']['first_name']
            data['sex'] = i['fields']['sex']
            data['province'] = i['fields']['province']
            data['city'] = i['fields']['city']
            data['industy'] = i['fields']['industy']
            data['job'] = i['fields']['job']
            data['email'] = i['fields']['email']
            data['company'] = i['fields']['company']
            data['header'] = i['fields']['image']
            data['detail'] = i['fields']['detail']
            # data['level'] = i['fields']['level']

        return HttpResponse(json.dumps({'status': True, 'data': data}), content_type='application/json')

    def post(self, request, *args, **kwargs):
        id = request.user.id
        name = request.POST.get('name')
        # username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        sex = request.POST.get('sex')
        province = request.POST.get('province')
        city = request.POST.get('city')
        industry = request.POST.get('industy')
        job = request.POST.get('job')
        detail = request.POST.get('detail')
        print(city, 22222222222222, job)
        email = request.POST.get('email')
        company = request.POST.get('company')
        obj = UserProfile.objects.get(id=id)
        # obj.username = username
        obj.name = name
        obj.sex = sex
        obj.detail = detail
        obj.province = province
        obj.city = city
        obj.industy = industry
        obj.job = job
        obj.email = email
        obj.company = company
        obj.save()

        return JsonResponse({'status': True, })


class Focus(APIView):
    def get(self, request):
        user = request.user.id
        page = request.GET.get('page')
        page = int(page)
        my_focus = Relationship.objects.filter(author=user)
        sum = my_focus.count()
        my_focus = my_focus[::-1]
        my_focus_list = my_focus[page * 5 - 5:page * 5]
        if my_focus:
            my_focus = serializers.serialize('json', my_focus_list)
            c = []
            for i in json.loads(my_focus):
                data = {}
                data['sum'] = sum
                data['User_ByID'] = i['fields']['User_ByID']
                User_ByID = i['fields']['User_ByID']
                data['relation_id'] = i['pk']
                for x in json.loads(serializers.serialize('json', UserProfile.objects.filter(id=User_ByID))):
                    data['name'] = x['fields']['username']
                    data['detail'] = x['fields']['detail']
                    data['header'] = x['fields']['image']

                c.append(data)
            return HttpResponse(json.dumps({'status': True, 'data': c}), content_type='application/json')
        else:
            return HttpResponse(json.dumps({'status': True, 'data': ''}), content_type='application/json')


class Fans(APIView):
    def get(self, request):
        user_id = request.user.id
        page = request.GET.get('page')
        page = int(page)
        my_fans = Relationship.objects.filter(User_ByID=user_id)
        sum = my_fans.count()
        my_fans = my_fans[::-1]
        my_fans_list = my_fans[page * 5 - 5:page * 5]
        if my_fans:
            my_fans = serializers.serialize('json', my_fans_list)
            c = []
            for i in json.loads(my_fans):
                data = {}
                data['sum'] = sum
                data['User_ByID'] = i['fields']['author']
                if Relationship.objects.filter(User_ByID=data['User_ByID'], author_id=user_id):
                    data['re_status'] = 1
                else:
                    data['re_status'] = 0
                User_ByID = i['fields']['author']
                data['relation_id'] = i['pk']
                for x in json.loads(serializers.serialize('json', UserProfile.objects.filter(id=User_ByID))):
                    data['name'] = x['fields']['username']
                    data['datail'] = x['fields']['detail']
                    data['header'] = x['fields']['image']

                c.append(data)
            return HttpResponse(json.dumps({'status': True, 'data': c}), content_type='application/json')
        else:
            return HttpResponse(json.dumps({'status': False}), content_type='application/json')


class Add_fans(APIView):
    def get(self, request):
        msg = {}
        user = request.user.id
        target = request.GET.get('target')
        if Relationship.objects.filter(author_id=user, User_ByID=target):
            msg['status'] = False
            msg['msg'] = '已关注'
            return HttpResponse(json.dumps({msg}), content_type='application/json')
        else:
            Relationship.objects.create(author_id=user, User_ByID=target)
            msg['status'] = True
            msg['msg'] = '关注成功'
            return HttpResponse(json.dumps(msg), content_type='application/json')


class Add_Focus(APIView):
    def get(self, request):
        msg = {}
        user = request.user.id
        target = request.GET.get('file_user_id')
        if user == target:
            msg['is_me'] = 1
            msg['status'] = False
            msg['msg'] = ''
            return JsonResponse(msg)
        else:
            if Relationship.objects.filter(author_id=user, User_ByID=target):
                msg['is_me'] = 0
                msg['is_focus'] = 1
                msg['status'] = False
                msg['msg'] = '已关注'
                return JsonResponse(msg)
            else:
                Relationship.objects.create(author_id=user, User_ByID=target)
                msg['is_me'] = 0
                msg['is_focus'] = 0
                msg['status'] = True
                msg['msg'] = '关注成功'
                return JsonResponse(msg)


class Delete_focus(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):  # delete my_foucus
        msg = {}
        id = request.POST.get('relation_id')
        file_id = Relationship.objects.get(id=id)
        file_id.delete()
        msg['status'] = True
        return HttpResponse(msg, content_type='application/json')


class Model(APIView):
    def get(self, request):
        try:
            id = request.user.id
            page = request.GET.get('page')
            page = int(page)
            # result = ModelResult.objects.filter(author=id)
            # data =
            # myData = serializers.serialize('json', ModelResult.objects.filter(user=id))
            myData = ModelResult.objects.filter(user=id)
            sum = myData.count()
            myData = myData[::-1]
            myData_list = myData[page * 12 - 12:page * 12]
            if myData:
                c = []
                myData = serializers.serialize('json', myData_list)
                for i in json.loads(myData):
                    data = {}
                    data['modelid'] = i['pk']
                    data['sum'] = sum
                    # data['label'] = [x for x in i['label'].values_list("name")]
                    data['name'] = i['fields']['ModelName']
                    data['share_status'] = i['fields']['is_share']
                    c.append(data)

                return JsonResponse({'status': True, 'json': c})
            else:
                return JsonResponse({'status': False, })
                return JsonResponse({'status': False, })
        except Exception as  e:
            print(e)

            return JsonResponse({'status': False})


def myNote(request):
    id = request.user.id
    msg = {'status': True, 'data': None}
    if request.method == 'POST':
        form = ProductForm(request.POST or None, request.FILES)
        print(form.data['title'])
        print(form.data['content'])
        if form.is_valid():
            item = MyNote()
            item.author_id = id
            item.title = form.data['title']
            item.content = form.data['content']
            item.save()
            msg['status'] = True
            msg['data'] = form.data

        else:
            msg['status'] = False
            msg['data'] = form.errors
        return JsonResponse(msg)
    else:
        id = request.GET.get('id')
        data = {}
        data['title'] = MyNote.objects.get(id=id).title
        data['content'] = MyNote.objects.get(id=id).content
        data['date'] = MyNote.objects.get(id=id).date.strftime('%Y-%m-%d')
        print(data['date'])
        return JsonResponse({'status': True, 'json': data})


def myscore(request):
    id = request.user.id
    if request.method == 'GET':
        myData = serializers.serialize('json', Myscore.objects.filter(author=id))
        data = {}
        for i in json.loads(myData):
            data['Score'] = i['fields']['Score']
            data['In_Score'] = i['fields']['In_Score']
            data['Out_Score'] = i['fields']['Out_Score']
            data['ScoreInfo'] = i['fields']['ScoreInfo']
        if Sign.objects.filter(author=id):
            for item in json.loads(serializers.serialize('json', Sign.objects.filter(author=id))):
                day = item['fields']['days']
                print(day)
                data['level'] = tests.progress_bar(day)[0]
                data['progess'] = ('%.2f%%' % ((tests.progress_bar(day)[1]) * 100))
                data['day'] = tests.progress_bar(day)[2]
        else:
            data['level'] = 0
            data['progess'] = 0
            data['day'] = 0

        return JsonResponse({'status': True, 'json': data})


class Collect_View(APIView):
    def get(self, request):
        action = request.GET.get('action')
        action = int(action)
        page = request.GET.get('page')
        page = int(page)
        user = request.user.id
        myData = serializers.serialize('json', Collect.objects.filter(user_id=user, source=action))
        l = []
        if myData:
            for i in json.loads(myData):
                l.append(i['fields']['file_id'])
            c = []
            l = l[::-1]
            if action == 1:
                sum = Collect.objects.filter(user_id=user, source=action).count()
                if sum == 0:
                    return JsonResponse({'status': False})
                for i in l[page * 9 - 9:page * 9]:
                    module = DataSource.objects.get(id=i)
                    data = {}
                    data['sum'] = sum
                    data['detail'] = module.detail
                    data['file_name'] = str(module.file_name)
                    # data['parent'] = i['fields']['parent']
                    data['label_name'] = [module.label_name]
                    data['create_time'] = module.create_time.strftime("%Y-%m-%d")
                    # (str(module.create_time)).split('T')[0]
                    data['views_num'] = module.view_num
                    data['download_num'] = module.download_num
                    data['thumb_num'] = module.thumb_num
                    data['id'] = module.pk
                    c.append(data)
                return JsonResponse({'status': True, 'json': c})
            elif action == 2:
                sum = Collect.objects.filter(user_id=user, source=action).count()
                if sum == 0:
                    return JsonResponse({'status': False})
                for i in l[page * 12 - 12:page * 12]:
                    module = Algorithms.objects.get(id=i)
                    data = {}
                    data['sum'] = sum
                    data['file_name'] = str(module.name)
                    data['label_name'] = [x for x in module.label.values_list("name")]
                    data['create_time'] = module.add_time.strftime("%Y-%m-%d")
                    data['views_num'] = module.view_num
                    data['thumb_num'] = module.thumb_num
                    data['download_num'] = module.download_num
                    data['id'] = module.pk
                    c.append(data)
                return JsonResponse({'status': True, 'json': c})
            else:
                sum = Collect.objects.filter(user_id=user, source=action).count()
                if sum == 0:
                    return JsonResponse({'status': False})
                for i in l[page * 12 - 12:page * 12]:
                    module = ModelResult.objects.get(id=i)
                    data = {}
                    data['file_name'] = str(module.ModelName)
                    data['sum'] = sum
                    data['label'] = [x for x in module.label.values_list("name")]
                    data['source'] = module.abstract
                    data['create_time'] = module.add_time.strftime("%Y-%m-%d")

                    data['id'] = module.pk
                    c.append(data)
                return JsonResponse({'status': True, 'json': c})
        return JsonResponse({'status': False, })


def delete_collect(request):
    user = request.user.id
    if request.method == 'GET':
        id = request.GET.get('id')
        file_id = SharingCollect.objects.filter(user_id=user, sharingfile_id=id)
        file_id.delete()

        return JsonResponse({'status': True, 'msg': '删除成功'})


class Algorithm_Upload(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        msg = {'status': True, 'error': None, 'success': None, 'data': None, 'datatype': None}
        user = request.user.id
        file = request.FILES.get("file", None)  # ｐｙ文件名
        _name = request.POST.get("name")  # 算法名称
        if not file:
            msg['error'] = '请选择算法文件'
            msg['status'] = False
            return JsonResponse(msg)
        filename = file.name
        filePostfix = os.path.splitext(filename)[1]
        _dtfilename = 'DF{0}{1}'.format(str(time.time()).replace('.', ''), filePostfix.upper())  # 格式化文件名
        filePath = os.path.join(settings.MEDIA_ROOT, _dtfilename)

        obj = Algorithms.objects
        author_id = request.user.id

        try:
            myHash = hashlib.md5()
            with open(filePath, 'wb+') as writer:
                for chunk in file.chunks():
                    writer.write(chunk)
                    myHash.update(chunk)
            fsize = os.path.getsize(filePath)
            fsize = fsize / float(1024)
            filesize = str(round(fsize, 2)) + 'KB'
            if os.path.splitext(filePath)[1] == '.py' or os.path.splitext(filePath)[1] == '.PY':
                try:
                    object_id = tests.save_mongo_py(filePath, author_id, filename)
                except Exception as  e:
                    return JsonResponse({'msg': '文件格式不正确！请重新上传', 'status': False})
            else:
                return JsonResponse({'msg': '文件格式不正确！请重新上传', 'status': False})
            author_id = UserProfile.objects.get(id=author_id)
            obj.create(name=filename, user=author_id, objid=object_id)
            mydata = serializers.serialize('json', Algorithms.objects.filter(objid=object_id))
            for i in json.loads(mydata):
                fileid = i['pk']
            return JsonResponse(
                {'status': True, 'filename': filename, 'type': filename.split('.')[1], 'fileid': fileid})
        except Exception as e:
            print(e)
            msg['error'] = '上传失败！'
            msg['status'] = False
            return JsonResponse(msg)


class Algorithm(APIView):
    def get(self, request):
        try:
            id = request.user.id
            page = request.GET.get('page')
            page = int(page)
            # myData = serializers.serialize('json', Algorithms.objects.filter(user=id))
            myData = Algorithms.objects.filter(user=id)
            sum = myData.count()
            myData = myData[::-1]
            myData_list = myData[page * 13 - 13:page * 13]
            if myData:
                c = []
                myData = serializers.serialize('json', myData_list)
                for i in json.loads(myData):
                    data = {}
                    data['name'] = i['fields']['name']
                    data['sum'] = sum
                    data['id'] = i['pk']
                    data['share_status'] = i['fields']['is_share']
                    try:
                        data['type'] = i['fields']['name'].split('.')[1]
                    except:
                        data['type'] = ''
                    c.append(data)
                return JsonResponse({'status': True, 'json': c})
            else:
                return JsonResponse({'status': False, })
        except:
            return JsonResponse({'status': False, })


class Delete_algorithm(APIView):
    def get(self, request):  # delete algorithm
        msg = {}
        id = request.GET.get('file_id')
        file_id = Algorithms.objects.filter(id=id)
        obj_id = file_id[0].objid
        file_id.delete()
        item = Collect.objects.filter(file_id=id)
        if item:
            item.delete()
        db.remove({"_id": ObjectId(obj_id)})
        msg['status'] = True
        return JsonResponse(msg)


class Delete_Data_Share(APIView):
    def get(self, request):
        try:
            fileid = request.GET.get('file_id')
            DataSource.objects.filter(pk=fileid).update(
                share_status=1)
            # SharingFile.objects.filter(title=DataSource.objects.get(pk=fileid).name, user_id=id).delete()
            return JsonResponse({'status': True, 'msg': 'sucessful'})
        except:
            return JsonResponse({'status': False, 'msg': 'failed'})


class Delete_Algorithm_Share(APIView):
    def get(self, request):
        try:
            fileid = request.GET.get('file_id')
            Algorithms.objects.filter(pk=fileid).update(
                is_share=0)
            # SharingFile.objects.filter(title=Algorithms.objects.get(pk=fileid).name, user_id=id).delete()
            return JsonResponse({'status': True, 'msg': 'sucessful'})
        except:

            return JsonResponse({'status': False, 'msg': 'failed'})


class Delete_Model_Share(APIView):
    def get(self, request):
        id = request.user.id
        if request.method == 'GET':
            fileid = request.GET.get('file_id')
            ModelResult.objects.filter(pk=fileid).update(
                is_share=1)
            # SharingFile.objects.filter(title=ModelResult.objects.get(pk=fileid).ModelName, user_id=id).delete()
        return JsonResponse({'status': True, 'msg': 'sucessful'})


class Algorithm_share(APIView):
    def get(self, request):  # share_algorithm
        # user = request.user.id
        # source = request.user.phone
        id = request.GET.get('file_id')
        type = request.GET.get('name')
        price = request.GET.get('price')
        desc = request.GET.get('desc')
        label = request.GET.get('label')
        myData = serializers.serialize('json', Algorithms.objects.filter(id=id))
        type_name = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        if type == '':
            type = type_name
        obj = AlgoLabel(name=label, second_name=type)
        try:
            obj.save()
            label = AlgoLabel.objects.filter(name=label, second_name=type).last()
            # print(AlgoLabel.objects.get(name=label, second_name=type).id)
            Algorithms.objects.filter(pk=id).update(is_share=1, price=int(price), abstract=desc)
            # for i in json.loads(myData):
            #     obj = AlgoLabel(score=price, desc=desc, label=label, title=i['fields']['name'],
            #                       content=i['fields']['OBJID'], user_id=user, category=3, source=source, tag=type)
            #     obj.save()
            item_b = AlgoLabel.objects.get(name=label, second_name=type)
            item_a = Algorithms.objects.get(pk=id)
            item_a.label.add(item_b)
            item_a.save()
            return JsonResponse({'status': True, 'msg': '共享成功'})
        except Exception:
            obj.delete()
            print(Exception)
            return JsonResponse({'status': False, 'msg': '共享失败'})


class Model_share(APIView):
    def get(self, request):  # share_algorithm
        try:
            # user = request.user.id
            # source = request.user.phone
            id = request.GET.get('file_id')
            type = request.GET.get('name')
            price = request.GET.get('price')
            desc = request.GET.get('desc')
            label = request.GET.get('label')
            # myData = serializers.serialize('json', Algorithms.objects.filter(id=id))
            obj = Model_Label(name=label, second_name=type)
            obj.save()
            label = Model_Label.objects.get(name=label, second_name=type)

            print(Model_Label.objects.get(name=label, second_name=type).id)
            ModelResult.objects.filter(pk=id).update(
                is_share=1, price=int(price), abstract=desc)
            # for i in json.loads(myData):
            #     obj = AlgoLabel(score=price, desc=desc, label=label, title=i['fields']['name'],
            #                       content=i['fields']['OBJID'], user_id=user, category=3, source=source, tag=type)
            #     obj.save()
            item_b = Model_Label.objects.get(name=label, second_name=type)
            item_a = ModelResult.objects.get(pk=id)
            item_a.label.add(item_b)
            item_a.save()
            return JsonResponse({'status': True, 'msg': '共享成功'})
        except Exception:
            print(Exception)
            return JsonResponse({'status': False, 'msg': '共享失败'})


class Delete_model(APIView):
    def get(self, request):  # delete algorithm
        msg = {}
        id = request.GET.get('file_id')
        file_id = ModelResult.objects.filter(id=id)

        file_id.delete()
        try:
            obj_id = file_id[0].OBJID
            db.remove({"_id": ObjectId(obj_id)})
        except:
            pass
        msg['status'] = True
        return JsonResponse(msg)


class Algorithm_Preview(APIView):
    def get(self, request):
        # if request.method == "GET":
        fileid = request.GET.get('id')
        print(fileid)
        obj_id = Algorithms.objects.get(id=fileid).OBJID
        print(obj_id)
        # for i in json.loads(mydata):
        #     obj_id = i['obj_id']
        result = db.find({'_id': ObjectId(obj_id)})

        data = (result[0]['fileData'])
        print(data)
        new_data = []
        for i in data:
            new_data.append(i.replace(' ', '&nbsp;'))
        # return JsonResponse({'status': True, 'data': new_data})
        return_json = {'status': True, 'data': new_data}
        return HttpResponse(json.dumps(return_json), content_type='application/json')


def sign(request):
    if request.method == 'GET':
        id = request.user.id
        try:
            obj = Sign.objects.get(author_id=id)
            if obj:
                if obj.Sign_Time.date() == datetime.datetime.now().date():
                    return JsonResponse({'status': False, 'msg': '今天已签到'})
                else:
                    score = serializers.serialize('json', Myscore.objects.filter(author=id))
                    for i in json.loads(score):
                        Myscore.objects.filter(author_id=id).update(
                            Score=i['fields']['Score'] + 10)
                    obj.days = obj.days + 1
                    obj.save()
                    for item in json.loads(serializers.serialize('json', Sign.objects.filter(author=id))):
                        day = item['fields']['days']
                        level = tests.progress_bar(day)[0]
                        UserProfile.objects.filter(id=id).update(level=level)
                    return JsonResponse({'status': False, 'msg': '签到成功'})


        except:
            pass


def sign_status(request):
    if request.method == 'GET':
        id = request.user.id
        try:
            obj = Sign.objects.get(author_id=id)
            print(obj)
            if obj:
                if obj.Sign_Time.date() == datetime.datetime.now().date():
                    return JsonResponse({'status': True, 'msg': '今天已签到'})


        except Exception as  e:
            pass


class Header(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        id = request.user.id
        photo = request.FILES['photo']
        old_header = serializers.serialize('json', UserProfile.objects.filter(pk=id))
        for i in json.loads(old_header):
            global old
            old = i['fields']['image']
        if photo:
            phototime = request.user.username + str(time.time()).split('.')[0]
            photo_last = str(photo).split('.')[-1]
            photoname = 'image/%s.%s' % (phototime, photo_last)
            img = Image.open(photo)
            img.save('media/' + photoname)
            filePath = os.path.join('media/', photoname)
            fsize = os.path.getsize(filePath)
            fsize = fsize / float(1024)
            if fsize > 50:
                os.remove(os.path.join('media/', photoname))
                return JsonResponse({'status': False, 'msg': '文件过大,上传图片请保持在50kb以内'})
            if UserProfile.objects.get(pk=id).image == 'image/default.jpg':
                pass
            elif UserProfile.objects.get(pk=id).image:
                os.remove(os.path.join('media', old))
            else:
                UserProfile.objects.filter(pk=id).update(
                    image=photoname)
            count = UserProfile.objects.filter(pk=id).update(
                image=photoname
            )
            # os.remove(os.path.join('media',old))
            if count:
                data = serializers.serialize('json', UserProfile.objects.filter(pk=id))
                print(data)
                for i in json.loads(data):
                    header = i['fields']['image']
                    return JsonResponse({'status': True, 'msg': '上传成功', 'data': header})
            else:
                return HttpResponse('上传失败')

        return HttpResponse('图片为空')


from django.contrib.auth.hashers import make_password


class Change_passwd(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        old_pwd = request.POST.get('old_pwd')
        pwd1 = request.POST.get('pwd1')
        pwd2 = request.POST.get('pwd2')
        if user.check_password(old_pwd):
            if pwd1 == pwd2:
                user.password = make_password(pwd1)
                user.save()
                return HttpResponse(json.dumps({'status': True, 'data': request.data}), content_type='application/json')
            else:
                HttpResponse(json.dumps({'status': False, 'data': request.data}), content_type='application/json')
        else:
            return HttpResponse(json.dumps({'status': False, 'data': request.data}), content_type='application/json')


class MyCourseView(APIView):
    def get(self, request):
        courses = MyCourse.objects.all()
        courses_serializer = MyCourseSerializer(courses, many=True)
        return Response(courses_serializer.data)


class MyLevel(APIView):
    """我的会员等级，存储空间，存储标签"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        id = request.user.id
        obj = UserLevel.objects.get(id=id)
        money = UserProfile.objects.get(id=id).money  # 余额
        consume = UserProfile.objects.get(id=id).consume  # 消费
        allmoney = int(money) + int(consume)
        if allmoney > OperationSettings.objects.filter(level=2).expenditure:
            UserProfile.objects.filter(id=id).update(member_level=2)
            StorageLabel.objects.filter(user_id=id).update(storage=2)
            obj.up_load = OperationSettings.objects.filter(level=2).storage  # 40MB
            obj.save()
            if allmoney > OperationSettings.objects.filter(level=3).expenditure:
                UserProfile.objects.filter(id=id).update(member_level=3)
                StorageLabel.objects.filter(user_id=id).update(storage=3)
                obj.up_load = OperationSettings.objects.filter(level=3).storage  # 60MB
                obj.save()
                if allmoney > OperationSettings.objects.filter(level=4).expenditure:
                    UserProfile.objects.filter(id=id).update(member_level=4)
                    StorageLabel.objects.filter(user_id=id).update(storage=4)
                    obj.up_load = OperationSettings.objects.filter(level=4).storage  # 80MB
                    obj.save()
                    if allmoney > OperationSettings.objects.filter(level=5).expenditure:
                        UserProfile.objects.filter(id=id).update(member_level=5)
                        StorageLabel.objects.filter(user_id=id).update(storage=5)
                        obj.up_load = OperationSettings.objects.filter(level=5).storage  # 100MB
                        obj.save()
        else:
            UserProfile.objects.filter(id=id).update(member_level=1)
            StorageLabel.objects.filter(user_id=id).update(storage=1)
            obj.up_load = OperationSettings.objects.filter(level=1).storage  # 20MB
            obj.save()
        up_load = obj.up_load
        lable = StorageLabel.objects.get(user_id=id).storage
        member_level = UserProfile.objects.get(id=id).member_level
        return_json = {"status": True, "up_load": up_load, "lable": lable, "member_level": member_level}
        return HttpResponse(json.dumps(return_json), content_type='application/json')


# 以下这些import的是为了查看个人中心详情页面
cli = pymongo.MongoClient(settings.MONGO_DB_URI)
from django_filters.rest_framework import DjangoFilterBackend
from personalcenter.models import Collect, Love
from rest_framework import filters
import base64
from algorithm import models
from utils.logConf import log

logger = log(__name__)


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


# 查看个人中心详情页面
class AlgoDetailViewSet(viewsets.GenericViewSet,
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
    queryset = Algorithms.objects.filter().all()
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


class FellBack(APIView):
    def get(self, request):
        try:
            title = request.GET.get('title')
            content = request.GET.get('content')
            contact = request.GET.get('contact')
            item = UserFellBack()
            item.title = title
            item.content = content
            item.contact = contact
            item.save()
            return_json = {'status': True, 'msg': '用户反馈成功'}
            return HttpResponse(json.dumps(return_json), content_type='application/json')
        except Exception as e:
            return_json = {'status': False, 'msg': '用户反馈失败'}
            return HttpResponse(json.dumps(return_json), content_type='application/json')
