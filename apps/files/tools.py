import chardet
import pymongo
import pandas as pd
import math
import re

from bson.objectid import string_type
from Datahoop.settings import MONGO_DB_URI


def Time(a):
    h = int(24 * a)
    min = int((24 * a - int(24 * a)) * 60)
    second = int((24 * a - int(24 * a)) * 60 - int((24 * a - int(24 * a)) * 60)) * 60
    h = str(h).zfill(2)  # 个位数自动补0
    min = str(min).zfill(2)
    second = str(second).zfill(2)
    return ("%s:%s:%s") % (h, min, second)


def save_mongo_txt(file, author_id, isHeader, separator, filename):
    try:
        client = pymongo.MongoClient(MONGO_DB_URI)
        db = client.datahoop.data
        with open(file, 'rb') as f:  # 判断文件的编码
            data_type = chardet.detect(f.readline())['encoding']
        with open(file, 'r', encoding=data_type, errors='ignore') as f1:
            data = pd.read_csv(f1, delimiter=separator, dtype=str)
        print(type(data))
        fileName = filename.replace((filename.split('.')[-1]), (filename.split('.')[-1]).lower()).replace(
            (filename.split('.')[-1]), (filename.split('.')[-1]).lower())
        if isHeader == 1:
            Data = [list(data.columns)] + data.values.tolist()
        else:
            all = data.shape[1]
            len_lines = []
            for i in range(all):
                len_lines.append('_C' + str(i))
            Data = [list(len_lines)] + [list(data.columns)] + data.values.tolist()
        jsonData = {
            'fileName': fileName,
            'userID': author_id,
            'fileData': Data
        }
        object_id = db.insert(jsonData)
        object_id = string_type(object_id)
        client.close()
        return object_id
    except Exception as e:
        return 'none'


def save_mongo_csv(file, author_id, isHeader, separator, filename):
    try:
        client = pymongo.MongoClient(MONGO_DB_URI)
        db = client.datahoop.data
        with open(file, 'rb') as f:  # 判断文件的编码
            data_type = chardet.detect(f.readline())['encoding']
        with open(file, 'r', encoding=data_type, errors='ignore') as f1:
            data = pd.read_csv(f1, delimiter=separator, dtype=str).dropna(axis=1, how='all')
        fileName = filename.replace((filename.split('.')[-1]), (filename.split('.')[-1]).lower()).replace(
            (filename.split('.')[-1]), (filename.split('.')[-1]).lower())
        if isHeader == 1:
            Data = [list(data.columns)] + data.values.tolist()
            # print(data.values.tolist())
        else:
            all = data.shape[1]
            len_lines = []
            for i in range(all):
                len_lines.append('_C' + str(i))
            Data = [list(len_lines)] + [list(data.columns)] + data.values.tolist()
            # print(Data)
        jsonData = {
            'fileName': fileName,
            'userID': author_id,
            'fileData': Data
        }
        object_id = db.insert(jsonData)
        object_id = string_type(object_id)
        # print(jsonData)
        client.close()
        return object_id
    except Exception as e:
        return 'none'


def save_mongo_sql(file, author_id):
    client = pymongo.MongoClient(MONGO_DB_URI)
    db = client.datahoop.data
    data_list = []
    with open(file, 'rb') as f:  # 判断文件的编码
        data_type = chardet.detect(f.readline())['encoding']
    with open(file, 'r', encoding=data_type, errors='ignore') as f1:
        for i in f1.readlines():
            data_list.append(re.findall(r'[^()]+', i.replace("'", ''))[1].split(','))
    data_list_table = []
    for i in range(len(data_list[0])):
        data_list_table.append('_C' + str(i))
    data_list.insert(0, data_list_table)
    jsonData = {
        'fileName': file.rsplit('\\', 1)[-1],
        'userID': author_id,
        'fileData': data_list
    }
    object_id = db.insert(jsonData)
    object_id = string_type(object_id)
    client.close()
    return object_id


def thirdry(author_id):
    client = pymongo.MongoClient(MONGO_DB_URI)
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
    client = pymongo.MongoClient(MONGO_DB_URI)
    db = client.datahoop.data
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
    # 删除存在本地的文件，本地不做保存
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
