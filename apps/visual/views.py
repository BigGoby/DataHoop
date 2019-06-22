import time
import json

from rest_framework.response import Response
from rest_framework import status
from rest_framework import views
from rest_framework.permissions import IsAuthenticated

from files.models import DataSource
from .serializers import UserFileSerializer

import pymongo
from bson import ObjectId
from datahoop21.settings import MONGO_DB_URI

from demoCelery.tasks import agg_func
from django.db.models import Q


# Create your views here.


class GetUserFiles(views.APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        data = DataSource.objects.filter(Q(user=self.request.user) & ~Q(obj_id='')).order_by('-id')
        file_data = []
        for i in data:
            file_data.append([i.file_name.name, i.obj_id])
        return Response(file_data)


class GetFileTitle(views.APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        obj_id = request.query_params['obj_id']
        data = DataSource.objects.filter(user=request.user, obj_id=obj_id)
        if data:
            mg_client = pymongo.MongoClient(MONGO_DB_URI)
            db = mg_client.datahoop.data
            title = db.find_one({'_id': ObjectId(obj_id)})['fileData'][0]
            name = str(data[0].file_name)
            return Response({'title': title, 'name': name})


import pandas as pd


class GetFileData(views.APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        obj_id = request.data['obj_id']
        dim = json.loads(request.data['dim'])
        value_agg = json.loads(request.data['value_agg'])
        agg = agg_func.delay(obj_id, '', dim, value_agg)
        while agg.status == 'PENDING':
            time.sleep(1)
            pass
        if agg.status == 'SUCCESS':
            rel = json.loads(agg.result)
            empty = pd.DataFrame()
            data = empty.append(rel["data"])
            rel["data"] = data.fillna('').values.tolist()
            rel = json.dumps(rel)

            return Response({'status': '0', 'data': rel})
        else:
            return Response({'status': '1', 'msg': '请检查数据格式', 'error': agg.result})
