# -*- coding: utf-8 -*-
import xadmin
from .models import ProjectCenter, BidDetails


class ProjectCenterAdmin(object):
    list_display = ['user', 'name', 'status', 'organizers', 'end_time', 'money', 'details', 'labels', 'count',
                    'add_time', 'area', 'pledge', 'key_word', 'click_num', 'finish_time', 'technology', 'standard',
                    'attention', 'download']
    search_fields = ['user__username', 'name', 'status', 'organizers', 'money', 'details', 'labels', 'count', 'area',
                     'pledge', 'key_word', 'click_num', 'technology', 'standard',
                     'attention', 'download']
    list_filter = ['user__username', 'name', 'status', 'organizers', 'end_time', 'money', 'details', 'labels', 'count',
                   'add_time', 'area', 'pledge', 'key_word', 'click_num', 'finish_time', 'technology', 'standard',
                   'attention', 'download']


class BidDetailsAdmin(object):
    list_display = ['project', 'user', 'bid_time', 'bid_price', 'end_time', 'remark', 'contact', 'select', 'ensure',
                    'inform', 'add_time']
    search_fields = ['project__name', 'user__username', 'bid_price', 'remark', 'contact', 'select', 'ensure', 'inform']
    list_filter = ['project__name', 'user__username', 'bid_time', 'bid_price', 'end_time', 'remark', 'contact',
                   'select', 'ensure', 'inform', 'add_time']


xadmin.site.register(ProjectCenter, ProjectCenterAdmin)
xadmin.site.register(BidDetails, BidDetailsAdmin)
