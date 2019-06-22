import xadmin

from .models import Relationship
from .models import Collect
from .models import MyCourse, UserFellBack, OperationSettings


class RelationshipAdmin(object):
    list_display = ("id", "Re_Status", "User_ByID", "author",)


xadmin.site.register(Relationship, RelationshipAdmin)


class CollectAdmin(object):
    list_display = (
        'user',
        'file_id',
        'source',
        'add_time',)


xadmin.site.register(Collect, CollectAdmin)


# class MyNoteAdmin(object):
#     list_display = ("id", "author", "title", "content","date","share_status")
# xadmin.site.register(MyNote,MyNoteAdmin)
#
#
# class MyscoreAdmin(object):
#     list_display = ("id", "author", "Score", "In_Score", "Out_Score", "ScoreInfo")
# xadmin.site.register(Myscore,MyscoreAdmin)

class MyCourseAdmin(object):
    list_display = ['student', 'course', 'time']


xadmin.site.register(MyCourse, MyCourseAdmin)


class UserFellBackAdmin(object):
    list_display = ['title', 'content', 'contact', 'add_time']
    search_fields = ['title', 'content', 'contact']
    list_filter = ['title', 'content', 'contact', 'add_time']


xadmin.site.register(UserFellBack, UserFellBackAdmin)


class OperationSettingsAdmin(object):
    list_display = ['id', 'level', 'expenditure', 'storage', 'storage_price', 'storage_discount_m',
                    'storage_discount_y', 'score', 'rhino_s', 'rhino_s_price', 'rhino_s_discount', 'time']


xadmin.site.register(OperationSettings, OperationSettingsAdmin)
