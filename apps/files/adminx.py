import xadmin
from .models import DataSource
from .models import DataSourcelLabel

from .models import UserLabel
from .models import AlgoLabel
from .models import StorageLabel
from .models import Association
from .models import Model_Label
from .models import WeCourse


class DataSourceAdmin(object):
    list_display = [
        'user',
        'file_name',
        'format_filename',
        'share_status',
        'create_time',
        'fileSize',
        'obj_id',
        'row_num',
        'column_num',
        'download_num',
        'fav_num',
        'view_num',
        'thumb_num',
        'title',
        'price',
        'where',
        'column_delimiter',
        'row_delimiter',
        'is_header',
        'detail',
        'category',
        'parent',
        'label_name',
    ]
    search_fields = ['user__username', 'file_name', 'parent']


xadmin.site.register(DataSource, DataSourceAdmin)


class DataSourcelLabelAdmin(object):
    list_display = [
        'name',
        'parent',
        'weight',
        'opweight',
        'remark',
        'status']


xadmin.site.register(DataSourcelLabel, DataSourcelLabelAdmin)


class UserLabelAdmin(object):
    list_display = ['name', 'level', 'parent', 'weight', 'opweight', 'contribution_rate', 'remark', 'status', ]


xadmin.site.register(UserLabel, UserLabelAdmin)


class AlgoLabelAdmin(object):
    list_display = [
        'type',
        'name',
        'second_name',
        'weight',
        'opweight',
        'remark',
        'status']


xadmin.site.register(AlgoLabel, AlgoLabelAdmin)


class ModelLabelAdmin(object):
    list_display = [
        'type',
        'name',
        'second_name',
        'weight',
        'opweight',
        'remark',
        'status']


xadmin.site.register(Model_Label, ModelLabelAdmin)


class StorageLabelAdmin(object):
    list_display = ['storage', 'name', 'opweight', 'remark', 'status']


xadmin.site.register(StorageLabel, StorageLabelAdmin)


class AssociationAdmin(object):
    list_display = ['name', 'level', 'parent', 'weight', 'opweight', 'remark', 'status',

                    ]


xadmin.site.register(Association, AssociationAdmin)


class WeCourseAdmin(object):
    list_display = ['user', 'name', 'label', 'abstract', 'content', 'cover', 'main_push', 'view_num',
                    "thumb_num", "is_buy", "price", 'create_time'
                    ]
    search_fields = ['name', 'label', 'abstract', 'content', 'cover', 'main_push', 'view_num',
                     "thumb_num", "is_buy", "price", ]
    list_filter = ['user', 'name', 'label', 'abstract', 'content', 'cover', 'main_push', 'view_num',
                   "thumb_num", "is_buy", "price", 'create_time']
    style_fields = {"content": "ueditor"}


xadmin.site.register(WeCourse, WeCourseAdmin)
