import pymongo
import csv
import pymysql
import re
import os
import math

from bson.objectid import string_type
from django.conf import settings


def Time(a):
    h = int(24 * a)
    min = int((24 * a - int(24 * a)) * 60)
    second = int((24 * a - int(24 * a)) * 60 - int((24 * a - int(24 * a)) * 60)) * 60
    h = str(h).zfill(2)  # 个位数自动补0
    min = str(min).zfill(2)
    second = str(second).zfill(2)
    return ("%s:%s:%s") % (h, min, second)


def save_mongo_txt(file, author_id, isHeader, separator, filename):
    client = pymongo.MongoClient(settings.MONGO_DB_URI)
    db = client.datahoop.data
    print(isHeader, 'pppppppppppppppppppppp')
    try:
        data = open(file, encoding='utf-8')
        fileName = filename.replace((filename.split('.')[-1]), (filename.split('.')[-1]).lower())
        fileData = []
        if isHeader == "True":
            for line in data:
                fileData.append(line.replace('\n', '').split(separator))
        else:
            all_len_lines = []

            for line in data:
                all_len_lines.append(len(line.replace('\n', '').split(separator)))
                fileData.append(line.replace('\n', '').split(separator))
            len_lines = []
            for i in range(max(all_len_lines)):
                len_lines.append('A' + str(i + 1))
            fileData.insert(0, len_lines)
        print(fileData)
        print('ppp')
        jsonData = {
            'fileName': fileName,
            'userID': author_id,
            'fileData': fileData
        }

    except Exception as e:
        data = open(file, encoding='gb18030', errors='ignore')
        fileName = filename.replace((filename.split('.')[-1]), (filename.split('.')[-1]).lower())
        fileData = []
        if isHeader == "True":
            for line in data:
                fileData.append(line.replace('\n', '').split(separator))
            print(fileData)
            print('ooo')
            print('dddddddddddddddddddddddddddddddddd')
        else:
            all_len_lines = []

            for line in data:
                all_len_lines.append(len(line.replace('\n', '').split(separator)))
                fileData.append(line.replace('\n', '').split(separator))
            len_lines = []
            for i in range(max(all_len_lines)):
                len_lines.append('A' + str(i + 1))
            fileData.insert(0, len_lines)
            print(fileData)
            print('ooo')

        jsonData = {
            'fileName': fileName,
            'userID': author_id,
            'fileData': fileData
        }

    object_id = db.insert(jsonData)
    object_id = string_type(object_id)
    client.close()
    os.remove(file)  # 删除存在本地的文件，本地不做保存
    return object_id


def save_mongo_csv(file, author_id, isHeader, separator, filename):
    client = pymongo.MongoClient(settings.MONGO_DB_URI)
    db = client.datahoop.data
    try:
        fr = open(file, mode='r', encoding='gbk')
        dlm = separator
        csv_reader = csv.reader(fr, delimiter=dlm)
        data = list(csv_reader)
        print(data)
        fileName = filename.replace((filename.split('.')[-1]), (filename.split('.')[-1]).lower()).replace(
            (filename.split('.')[-1]), (filename.split('.')[-1]).lower())
        fileData = []
        if isHeader == "True":
            for line in data:
                fileData.append(line)
        else:
            all_len_lines = []

            for line in data:
                all_len_lines.append(len(line))
                fileData.append(line)
            len_lines = []
            for i in range(max(all_len_lines)):
                len_lines.append('A' + str(i + 1))
            fileData.insert(0, len_lines)
            print(fileData)
            print('ooo')

        jsonData = {
            'fileName': fileName,
            'userID': author_id,
            'fileData': fileData
        }

        object_id = db.insert(jsonData)
        object_id = string_type(object_id)
    except Exception as e:
        fr = open(file, mode='r')
        dlm = separator
        csv_reader = csv.reader(fr, delimiter=dlm)
        data = list(csv_reader)
        print(data)
        fileName = filename.replace((filename.split('.')[-1]), (filename.split('.')[-1]).lower())
        fileData = []
        if isHeader == "True":
            for line in data:
                fileData.append(line)
        else:
            all_len_lines = []

            for line in data:
                all_len_lines.append(len(line))
                fileData.append(line)
            len_lines = []
            for i in range(max(all_len_lines)):
                len_lines.append('A' + str(i + 1))
            fileData.insert(0, len_lines)
            print(fileData)
            print('ooo')
        jsonData = {
            'fileName': fileName,
            'userID': author_id,
            'fileData': fileData
        }

        object_id = db.insert(jsonData)
        object_id = string_type(object_id)

    client.close()
    os.remove(file)  # 删除存在本地的文件，本地不做保存
    return object_id


def save_mongo_sql(file, author_id):
    import subprocess
    # sql = 'mysql --defaults-extra-file=/etc/mysql/fabric.cfg testmysql < %s' % file
    sql = 'mysql  testsql < %s' % file
    subprocess.call(sql, shell=True)
    content = open(file).read()
    table_name = (re.findall("DROP TABLE IF EXISTS `(.+)`", content))[0]
    client = pymongo.MongoClient(settings.MONGO_DB_URI)
    db = client.datahoop.data
    con = pymysql.connect('172.17.0.100', 'root', 'root', 'testsql')
    with con:
        # 仍然是，第一步要获取连接的 cursor 对象，用于执行查询
        cur = con.cursor()
        sql = "select DISTINCT (COLUMN_NAME) from information_schema.COLUMNS where table_name = '%s'"
        cur.execute(sql % (table_name))
        rows = cur.fetchall()
        rels = []
        rel = []
        for i in rows:
            rel.append(i[0])
        rels.append(rel)
        # 类似于其他语言的 query 函数， execute 是 python 中的执行查询函数
        cur.execute("SELECT * FROM  %s" % (table_name))
        # 使用 fetchall 函数，将结果集（多维元组）存入 rows 里面
        rows = cur.fetchall()
        # 依次遍历结果集，发现每个元素，就是表中的一条记录，用一个元组来显示
        for row in rows:
            rels.append(list(row))
        jsonData = {
            'fileName': table_name + '.sql',
            'userID': author_id,
            'fileData': rels
        }
        object_id = db.insert(jsonData)
        object_id = string_type(object_id)
        client.close()
        cur.close()
        os.remove(file)  # 删除存在本地的文件，本地不做保存
        return object_id


def thirdry(author_id):
    client = pymongo.MongoClient(settings.MONGO_DB_URI)
    db = client.netease_music.song
    a = []
    for i in db.find().limit(1):
        a.append(list(i)[1:])
    for i in (db.find({}).limit(1000)):
        s = []
        for item in list(i)[1:]:
            s.append(i[item])
        a.append(s)
    jsonData = {
        'fileName': 'netease',
        'userID': author_id,
        'fileData': a
    }

    object_id = db.insert(jsonData)
    object_id = string_type(object_id)

    client.close()
    return object_id


def save_mongo_py(file, author_id, filename):
    client = pymongo.MongoClient(settings.MONGO_DB_URI)
    db = client.mae
    try:
        data = open(file, encoding='utf-8')
        fileName = filename.replace((filename.split('.')[-1]), (filename.split('.')[-1]).lower())
        fileData = []
        for line in data:
            fileData.append(line)
        jsonData = {
            'fileName': fileName,
            'userID': author_id,
            'fileData': fileData
        }

    except Exception as e:
        data = open(file, encoding='gbk')
        fileName = filename.replace((filename.split('.')[-1]), (filename.split('.')[-1]).lower())
        fileData = []
        for line in data:
            fileData.append(line)
        jsonData = {
            'fileName': fileName,
            'userID': author_id,
            'fileData': fileData
        }

    object_id = db.insert(jsonData)
    object_id = string_type(object_id)
    client.close()
    data.close()
    os.remove(file)  # 删除存在本地的文件，本地不做保存
    return object_id


# 登陆天数n   等级k  升级剩余天数res   进度条bar   (k-1)*(k-1)+4*(k-1)<n<k*k+4*k

def progress_bar(n):
    k = int(math.sqrt(n + 4)) - 1
    bar = round((n - ((k - 1) * (k - 1) + 4 * (k - 1))) / (2 * k + 3), 2)
    if bar == 1:
        k = k + 1
        res = 2 * k + 5
        bar = 0
    else:
        k = k
        res = k * k + 4 * k - n
    return (k, bar, res)
    # print(progress_bar(10190))
