import os
import django

os.environ.update({"DJANGO_SETTINGS_MODULE": "DataHoop.settings"})
django.setup()

from users.models import UserLevel, UserProfile


# 用户注册默认信息设置
class DefaultSetting:
    '''用户信息的默认值设置'''

    def newuser(self, pk):
        UserLevel.objects.create(user_id=pk, name='', core=0, ram='', memory='', up_load=20, csv=True,
                                 txt=True, sql=True, mySQL=True, postgreSQL=False, SQLsever=False,
                                 sol_data=False, octopus=False, delete=True, diyfill=True,
                                 f_upper=True, upper=True, letter=True, union=True, textclassify=True,
                                 prevfill=True, netxfill=True, de_value=True, outliers=True, scaler=True,
                                 PCA=True, FA=True, onegotencode=True, labelencode=True, discretization=True,
                                 polynomial=True, histogram=True, pie=True, scatter=True, bar=True, brokenline=True,
                                 radar=True, heatmap=True, bubble=True, funnel=True, algorithms=True)


# 读取已经存在的用户id，来创建UserProfile表内容
if __name__ == '__main__':
    # UserLevel中的所有user_id（外键关联UserProfile）
    userlevel_userid = []
    for i in UserLevel.objects.all():
        userlevel_userid.append(i.user_id)

    # UserProfile中的所有id
    for j in UserProfile.objects.all():
        if j.id in userlevel_userid:
            print('user_id%s已存在，不需要设置默认参数' % (j.id))
        else:
            obj = DefaultSetting()
            obj.newuser(j.id)
            print('user_id%s创建完默认参数' % (j.id))
    print('%s用户默认参数创建成功' % (len(UserProfile.objects.all())))
