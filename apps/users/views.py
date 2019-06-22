import random
import re
import json

from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework_jwt.serializers import jwt_encode_handler, jwt_payload_handler
from .models import UserProfile, VerifyCode
from .serializers import SmsSerializer, RegisterSerializer, UserDetailSerializer, ForgetPasswordSerializer
from utils.sms import sms
from rest_framework.views import APIView
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password


class UserExist(APIView):
    def post(self, request):
        """
        用户名是否存在

        url:/exist

        type:post

        data:{username:'用户名'}

        :param request:
        :return:
        """
        username = request.POST.get('username')
        item = UserProfile.objects.filter(Q(username=username) | Q(mobile=username))
        if item:
            return_json = {'status': True, 'data': None, 'msg': '用户名已存在'}
            return HttpResponse(json.dumps(return_json), content_type='application/json')
        else:
            return_json = {'status': False, 'data': None, 'msg': '用户名不存在'}
            return HttpResponse(json.dumps(return_json), content_type='application/json')


class CustomBackend(ModelBackend):
    """
    自定义用户认证
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = UserProfile.objects.get(Q(username=username) | Q(mobile=username))
            if user.check_password(password):
                return user
        except Exception as e:
            return None


class SmsCodeViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    发送短信验证码
    :status:0,成功
            1,失败
    """
    serializer_class = SmsSerializer

    def generate_code(self):
        """
        生成6位数字验证码
        :return:
        """
        seeds = '1234567890'
        random_str = []
        for i in range(6):
            random_str.append(random.choice(seeds))
        return ''.join(random_str)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mobile = serializer.validated_data['mobile']
        code = self.generate_code()

        result = sms(mobile, code)
        if result['result'] == 0:
            code_record = VerifyCode(code=code, mobile=mobile, type=request.data['type'])
            code_record.save()
            return Response({'status': 0, 'msg': '发送验证码成功。'})
        else:
            return Response({'status': 1, 'msg': '发送验证码出错。'}, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    """
    用户注册
    """
    queryset = UserProfile.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # if serializer.validated_data['type'] != 1:
        #     return Response({'status':1, 'msg': '注册失败'})
        user = self.perform_create(serializer)

        re_dict = serializer.data
        payload = jwt_payload_handler(user)
        re_dict['token'] = jwt_encode_handler(payload)
        headers = self.get_success_headers(serializer.data)
        # 新用户默认参数创建
        username = request.data['username']
        pk = UserProfile.objects.filter(username=username)
        pk_id = pk[0].id
        obj = per_info_def.DefaultSetting()
        obj.newuser(pk_id)

        return Response(re_dict, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        return serializer.save()

    def get_serializer_class(self):
        if self.action == 'create':
            return RegisterSerializer
        if self.action == 'retrieve':
            return UserDetailSerializer
        if self.action == 'update':
            return UserDetailSerializer
        return UserDetailSerializer


class ForgetPasswordViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    忘记密码
    """
    queryset = UserProfile.objects.all()
    serializer_class = ForgetPasswordSerializer
    lookup_field = 'mobile'

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = self.perform_update(serializer)

        re_dict = serializer.data
        payload = jwt_payload_handler(user)
        re_dict['token'] = jwt_encode_handler(payload)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(re_dict)

    def perform_update(self, serializer):
        return serializer.save()


class DirectRegister(APIView):
    """
        获取数据

        参数没有传空

        {
            type:post,

            url:/users/directregister/,

            data:{username:zhansan,password:123456},

            dataType:JSON,
        }
        """

    def post(self, request):
        return_msg_list = []
        password = '1234!@#$'
        password = make_password(password, None, 'pbkdf2_sha256')
        data = request.data['username']
        data_list = re.findall(r'\[.*?\]', data)
        try:
            request.data['key']
        except:
            return_json = {'status': False, 'data': None, 'msg': '令牌不正确'}
            return HttpResponse(json.dumps(return_json), content_type='application/json')
        if request.data['key'] != None:
            if request.data['key'] == '7f5028bc46c56d52073d2a1916572f83764f979ea429ccv7)@c?~':
                for l in data_list:
                    # ['sz06zhanchao','15862500954','361090979@qq.com']
                    l = eval(l)
                    item = UserProfile.objects.filter(Q(username=l[0]) | Q(mobile=l[0]))
                    if item:
                        return_msg_list.append('%s registration failed--用户名(%s)已存在' % (l[0], l[0]))
                    else:
                        try:
                            if l[1] == 'nan' and l[2] != 'nan':
                                UserProfile.objects.create(username=l[0], password=password, origin=2,
                                                           email=l[2])
                            elif l[2] == 'nan' and l[1] == 'nan':
                                UserProfile.objects.create(username=l[0], password=password, origin=2)
                            else:
                                try:
                                    UserProfile.objects.create(username=l[0], password=password, origin=2,
                                                               mobile=l[1],
                                                               email=l[2])
                                except:
                                    UserProfile.objects.create(username=l[0], password=password, origin=2,
                                                               email=l[2])
                            # 导入户默认参数创建
                            pk = UserProfile.objects.filter(username=l[0])
                            pk_id = pk[0].id
                            obj = per_info_def.DefaultSetting()
                            obj.newuser(pk_id)
                            # return_msg_list.append('%s registration ok' % l[0])
                        except:
                            return_msg_list.append('%s registration failed' % l[0])
                return_json = {'status': True, 'data': return_msg_list, 'msg': '令牌不正确'}
                return HttpResponse(json.dumps(return_json), content_type='application/json')
            else:
                return_json = {'status': False, 'data': None, 'msg': '令牌不正确'}
                return HttpResponse(json.dumps(return_json), content_type='application/json')
