# -*- coding: utf-8 -*-
import xadmin
from .models import Info


class InfoAdmin(object):
    list_display = ['user', 'title', 'click_num', 'add_time', 'content', 'desc', 'label']
    search_fields = ['user__username', 'title', 'click_num', 'content', 'desc', 'label']
    list_filter = ['user__username', 'title', 'click_num', 'add_time', 'content', 'desc', 'label']
    style_fields = {"content": "ueditor"}


xadmin.site.register(Info, InfoAdmin)
