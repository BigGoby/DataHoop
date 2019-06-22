from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework import mixins, generics, viewsets
from rest_framework.views import APIView
from .models import ProjectCenter, BidDetails
from .serializers import ProjectCenterSerializer, BidDetailsSerializer
from rest_framework.pagination import PageNumberPagination
from .filter import ProjectFilter
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from django.db.models import Q
import datetime
from rest_framework.permissions import IsAuthenticated
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.authentication import SessionAuthentication
from utils.permissions import IsOwnerOrReadOnly
from users.models import UserProfile


# from rest_framework_extensions.cache.mixins import CacheResponseMixin


# 项目分页
class ProjectPagination(PageNumberPagination):
    page_size = 10
    # page_size_query_param = 'page_size'
    # page_query_param = "p"
    # max_page_size = 100


# 项目搜索，排序，分页，筛选
class ProjectViewSet(mixins.ListModelMixin,
                     viewsets.GenericViewSet,
                     mixins.RetrieveModelMixin,
                     ):
    """
    项目中心与项目库接口

    项目搜索，排序，分页，筛选
    """
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    queryset = ProjectCenter.objects.filter(~Q(status='已删除')).all()
    serializer_class = ProjectCenterSerializer
    pagination_class = ProjectPagination

    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_class = ProjectFilter
    search_fields = ('name',)
    ordering_fields = ('count', 'publish_time',)
    ordering = ('-add_time',)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.click_num += 1
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class BidsView(APIView):
    '''
    竞标列表，参与竞标

    参数没有传空

    {

        type:get,

        url:/trade/bid/,

        data:{pro_id:'项目的id'},

        dataType:JSON,

    }

    {

        type:post,

        url:/trade/bid/,

        data:{pro_id:'项目的id',

              price:'价格'

              end_time:‘交付时间’

              remark:‘留言’

              contact:‘联系方式’

             },

        dataType:JSON,
    }


    '''

    def get(self, request):
        pro_id = request.GET.get('pro_id', '')
        thumb = BidDetails.objects.filter(project=pro_id).all()
        result = []
        pro_user = ProjectCenter.objects.get(id=pro_id).user_id
        if pro_user == request.user.id:
            result.append({'is_user': True})
        else:
            result.append({'is_user': False})
        for item in thumb:
            dic = {}
            dic['bid_time'] = item.bid_time
            dic['username'] = item.user.username
            dic['price'] = item.bid_price
            dic['end_time'] = item.end_time
            dic['remark'] = item.remark
            dic['contact'] = item.contact
            dic['ensure'] = item.ensure
            result.append(dic)
        return Response(result)

    def post(self, request):
        price = request.POST.get('price', '')
        end_time = request.POST.get('end_time', '')
        remark = request.POST.get('remark', '')
        contact = request.POST.get('contact', '')
        pro_id = request.POST.get('pro_id', '')
        pro_user = ProjectCenter.objects.get(id=pro_id).user_id
        if pro_user == request.user.id:
            msg = '无法竞标自己发布的项目！'
            return Response(msg)
        bid_user = BidDetails.objects.filter(project=pro_id, user=request.user.id)
        if bid_user:
            msg = '您已竞标过该项目，无法再次竞标！'
            return Response(msg)
        item = BidDetails()
        item.user = request.user.id
        item.bid_price = price
        item.end_time = end_time
        item.remark = remark
        item.contact = contact
        item.save()
        num = ProjectCenter.objects.get(id=pro_id)
        num.count += 1
        num.save()
        msg = '成功参与竞标！'
        return Response(msg)


class EnsureView(APIView):
    '''
    选中竞标者
    {

        type: update,

        url: /trade/ensure/,

        data: {pro_id: '项目的id'

           bid_user: '竞标人id或username'

           },

        dataType: JSON,
    }
    '''

    def post(self, request):
        pro_id = request.data.get('pro_id', '')
        bid_user = request.data.get('bid_user', '')
        BidDetails.objects.filter(project=pro_id, user=bid_user).update(ensure=True, select=True)
        msg = '已选中！'
        # 平台通知竞标者一被选中，等待发布者联系或主动联系发布者
        return Response(msg)


class MyProjectView(APIView):
    '''
    我的项目中心

    {

        type:get,

        url:/trade/myproject/,

        data:{click:'选择的按钮（我的项目，我竞标的项目，项目回收站）'

              num:当前页码},

        dataType:JSON,

    }

    {

        type:post,

        url:/trade/myproject/,

        data:{click:'操作方式（删除，恢复，彻底删除）'

              pro_id:'项目id'

             },

        dataType:JSON,
    }
    '''

    def get(self, request):
        click = request.GET.get('click', '')
        num = int(request.GET.get('num', 1))
        if click == '我的项目':
            thumb = ProjectCenter.objects.filter(~Q(status='已删除') & Q(user=request.user.id)).all()
            result = []
            # dic = {}
            # dic['total'] = thumb.count
            # result.append(dic)
            # print(dic,'11111111111111111111111111111111111111111`')
            for item in thumb:
                dic = {}
                dic['ID'] = item.id
                dic['name'] = item.name
                if item.end_time > datetime.datetime.now().date():
                    dic['state'] = '已截止'
                else:
                    dic['state'] = item.status
                dic['type'] = item.pro_type
                dic['organizers'] = item.organizers
                dic['end_time'] = item.end_time
                dic['money'] = item.money
                dic['num'] = item.count
                dic['total'] = thumb.count()
                # dic['total'] = item.count

                result.append(dic)
            print(num)
            if num == 1:
                result = result[num * (num - 1):(num * 10)]
            else:
                result = result[((num - 1) * 10) + 1:(num * 10)]
            return Response(result)

        elif click == '我竞标的项目':
            thumb = ProjectCenter.objects.filter(~Q(status='已删除') & Q(project_bid__user=request.user.id)).all()
            result = []
            for item in thumb:
                dic = {}
                dic['ID'] = item.id
                dic['name'] = item.name

                if item.end_time > datetime.datetime.now().date():
                    dic['state'] = '已截止'
                else:
                    dic['state'] = item.status
                dic['type'] = item.pro_type
                dic['organizers'] = item.organizers
                dic['end_time'] = item.end_time
                dic['money'] = item.money
                dic['num'] = item.count
                dic['ensure'] = BidDetails.objects.get(project=item.id).ensure
                dic['total'] = thumb.count()
                result.append(dic)
            if num == 1:
                result = result[num * (num - 1):(num * 10)]
            else:
                result = result[((num - 1) * 10) + 1:(num * 10)]
            return Response(result)

        else:
            thumb = ProjectCenter.objects.filter(status='已删除', user=request.user.id).all()
            result = []
            for item in thumb:
                # if item.del_time + datetime.timedelta(days=30) < datetime.datetime.now():
                dic = {}
                dic['ID'] = item.id
                dic['name'] = item.name
                dic['state'] = '已删除'
                dic['type'] = item.pro_type
                dic['organizers'] = item.organizers
                dic['end_time'] = item.end_time
                dic['money'] = item.money
                dic['num'] = item.count
                dic['total'] = thumb.count()
                result.append(dic)
                # else:
                #     ProjectCenter.objects.filter(id=item.id).delete()
            if num == 1:
                result = result[num * (num - 1):(num * 10)]
            else:
                result = result[((num - 1) * 10) + 1:(num * 10)]
            return Response(result)

    def post(self, request):
        click = request.data.get('click', '')
        pro_id = request.data.get('pro_id', '')
        if click == '删除':
            thumb = ProjectCenter.objects.get(id=pro_id)
            thumb.status = '已删除'
            thumb.save()
            # 平台消息通知参与竞标的人项目被发布者删除
            return Response('项目已移除至回收站,回收站只保存30天！')

        elif click == '恢复':
            thumb = ProjectCenter.objects.get(id=pro_id)
            thumb.status = '进行中'
            thumb.save()
            return Response('项目已恢复，请至我的项目查看！')

        else:
            ProjectCenter.objects.filter(id=pro_id).delete()
            return Response('项目已彻底删除')


class IssueView(APIView):
    def post(self, request):
        pro_type = request.POST.get('pro_type')
        name = request.POST.get('name')
        labels = request.POST.get('labels')
        details = request.POST.get('details')
        technology = request.POST.get('technology')
        finish_time = request.POST.get('finish_time')
        standard = request.POST.get('standard')
        download = request.POST.get('download')
        attention = request.POST.get('attention')
        end_time = request.POST.get('end_time')
        money = float(request.POST.get('money'))
        pledge = float(request.POST.get('pledge'))

        if money * 0.02 > UserProfile.objects.get(id=request.user.id).money:
            return Response('账户余额不足！')
        else:
            item = ProjectCenter()
            item.pro_type = pro_type
            item.name = name
            item.labels = labels
            item.details = details
            item.technology = technology
            item.finish_time = finish_time
            item.standard = standard
            item.download = download
            item.attention = attention
            item.end_time = end_time
            item.money = money
            item.pledge = pledge
            item.user_id = request.user.id
            # 保证金为项目奖金的2%
            item.save()
            return Response('项目发起成功！')
