import xadmin
from .models import UserLevel


class UserLevelAdmin(object):
    fields_list = ['id', 'user', 'core', 'ram', 'memory', 'up_load', 'csv', 'txt', 'sql', 'mySQL',
                   'postgreSQL', 'SQLsever', 'sol_data', 'octopus', 'delete', 'diyfill', 'f_upper',
                   'upper', 'letter', 'union', 'textclassify', 'prevfill', 'netxfill', 'de_value',
                   'outliers', 'scaler', 'PCA', 'FA', 'onegotencode', 'labelencode', 'discretization',
                   'polynomial', 'histogram', 'pie', 'scatter', 'bar', 'brokenline', 'radar', 'heatmap',
                   'bubble', 'funnel', 'algorithms']
    list_display = fields_list
    search_fields = ['user__username', 'id']
    list_filter = fields_list


xadmin.site.register(UserLevel, UserLevelAdmin)
