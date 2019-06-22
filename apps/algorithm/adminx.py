# -*- coding: utf-8 -*-
import xadmin
from .models import *


class AlgorithmAdmin(object):
    list_display = ['id', 'name', 'user', 'label', 'type', 'status', 'price', 'add_time']
    search_fields = ['user__username', 'name', 'labels']
    list_filter = ['user__username', 'name', 'status', 'add_time', 'label']


class AlgLabelAdmin(object):
    list_display = ['name', 'user']


class ModelResultAdmin(object):
    list_display = ['id', 'ModelName']


xadmin.site.register(Algorithms, AlgorithmAdmin)
xadmin.site.register(ModelResult, ModelResultAdmin)
