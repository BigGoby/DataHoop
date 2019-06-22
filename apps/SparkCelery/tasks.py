# coding: utf-8
# 59f03100b66db239f761f92f
# test_decision_boundary_fig
from .my_celery import app


@app.task
def add(x):
    print('11')
    return x


from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.sql import functions
import uuid
import os
import json
from . import test1
from SparkCelery.settings import filepath_DIR,filepath_result_DIR,filepath_model_DIR,mongodbUri,url

print(filepath_DIR,filepath_result_DIR,filepath_model_DIR,mongodbUri)

# 测试
@app.task
def TaskScheduling(last=None, next=None):
    last = {"defName": "a", "arg": 1}
    rel = ''
    if last != None:
        print("last !!!")
        print(last["defName"])
        rel = getattr(test1, last["defName"])(4)

        print(rel)

    if next != None:
        print("next !!!")
    rel = json.dumps(rel)
    return rel


##################################################################
@app.task
def DataSet(FilePath, sep, header):
    '''
    :param FilePath: 文件路径
    :param sep: 分隔符
    :param header: 是否包含表头 None or True
    :return: filepath1
    '''
    msg = {'status': True, 'error': None, 'data': None}
    try:
        NAME = "DataSet"
        CLASS = "Data_Process"
        spark = SparkSession.builder.appName("myModel").getOrCreate()
        FilePath1 = url+FilePath
        df = spark.read.csv(FilePath1, sep=sep, inferSchema=True, header=header, encoding="gbk")
        uuid_name = str(uuid.uuid1())
        filepath1 = os.path.join(filepath_DIR, uuid_name)
        df.write.csv(filepath1)
        df.show()
        out_result = {}
        out_result["function_name"] = NAME
        out_result["function_class"] = CLASS
        out_result["file_name"] = uuid_name
        out_result["filepath"] = filepath1
        msg["data"] = out_result
    except Exception as e:
        msg["status"] = False
        msg["error"] = '执行失败：%s' % e
    msg = json.dumps(msg)
    return msg


@app.task
def LogisticR_spark(filepath,feature_columns,label_columns,maxiter, regparam, elasticnetparam):
    '''
    :param filepath: 文件路径
    :param feature_columns: 特征变量 列号
    :param label_columns: 标签变量 列号
    :param maxiter: 迭代次数
    :param regparam: 正则化参数(>=0)
    :param elasticnetparam:Elasticnet混合参数，0-1之间，当为0时,惩罚为L2正则化，当为1时为L1正则化
    :return: 字典 模型展示结果存objct_id，预测拟合结果和模型存mongodb
    '''
    msg = {'status': True, 'error': None,  'data': None}
    try:
        NAME = "LogisticRegression"
        CLASS = "Classify"
        spark = SparkSession.builder.appName("myModel").getOrCreate()
        train_filepath = filepath[0]
        test_filepath = filepath[1]
        train_df = spark.read.csv(train_filepath,inferSchema=True)
        test_df = spark.read.csv(test_filepath, inferSchema=True)
        feature_colname = [train_df.columns[ii] for ii in feature_columns]
        featuresCreator = VectorAssembler(inputCols=feature_colname, outputCol="features")
        train_df.show()
        logr = LogisticRegression(maxIter=maxiter, regParam=regparam,
                                  elasticNetParam=elasticnetparam,labelCol=train_df.columns[label_columns],featuresCol="features")
        # 创建一个管道
        from pyspark.ml import Pipeline
        pipeline = Pipeline(stages=[featuresCreator, logr])
        model = pipeline.fit(train_df)
        test_model = model.transform(test_df)
        uuid_name1 = str(uuid.uuid1())
        filepath_result = os.path.join(filepath_result_DIR, uuid_name1)
        test_model.show()

        print(type(test_model),filepath_result)
        test_model.write.save(filepath_result)
        # uuid_name = str(uuid.uuid1())
        # file_result_DIR = "hdfs://master:9000/datahoop/filepath_result/"
        # filepath_result1 = os.path.join(file_result_DIR, uuid_name)
        # df11 = spark.read.parquet(filepath_result)
        # df11.write.csv(filepath_result1)
        # df11.show()
        Test_Model = test_model.toPandas()[0:21]
        Test_Model_title = list(Test_Model.columns)
        Test_Model_Result = [Test_Model_title] + Test_Model.values.tolist()
        #print(type(str(Test_Model_Result[1][8])),str(Test_Model_Result),"qqqqqqqqqqqqqqq")
        #评价模型性能
        evaluator = BinaryClassificationEvaluator(rawPredictionCol="probability",labelCol=train_df.columns[label_columns])
        #测试预测结果和模型以路径形式存hdfs
        #from pyspark.ml import PipelineModel
        uuid_name2 = str(uuid.uuid1())
        filepath_model = os.path.join(filepath_model_DIR, uuid_name2)
        model.write().overwrite().save(filepath_model)
        output = {}
        output["function_name"] = NAME
        output["function_class"] = CLASS
        output["Test_Model_Result"] = str(Test_Model_Result)
        output["areaUnderROC"] = float(evaluator.evaluate(test_model,{evaluator.metricName: "areaUnderROC"}))
        output["areaUnderPR"] = float(evaluator.evaluate(test_model,{evaluator.metricName: "areaUnderPR"}))
        import pymongo
        from bson.objectid import string_type
        #from settings import mongodbUri
        client = pymongo.MongoClient(mongodbUri)
        db = client.mark.algo_collection
        jsonData = {
            'fileName': NAME,
            'userID': 2,
            'fileData': output
        }
        OBJ = db.insert(jsonData)
        OBJ_ID = string_type(OBJ)
        client.close()
        out_result = {}
        out_result["OBJ_ID"] = OBJ_ID
        out_result["file_name"] = [uuid_name1,uuid_name2]
        out_result["filepath"] = [filepath_result,filepath_model]
        msg["data"] = out_result
    except Exception as e:
        msg["status"] = False
        msg["error"] = '执行失败：%s' % e
    msg = json.dumps(msg)
    return msg


@app.task
def Sample(FilePath, ratio):
    spark = SparkSession.builder.appName("myModel").getOrCreate()
    # df = spark.read.csv(FilePath,inferSchema=True,encoding="gbk",sep=",",header=True)
    df = spark.read.csv(FilePath)
    df.show()
    Ratio = [ratio, 1 - ratio]
    (trainData, testData) = df.randomSplit(Ratio)
    uuid_name = str(uuid.uuid1())
    file_DIR = "hdfs://master:9000/datahoop/filepath/"
    trainData_filepath = os.path.join(file_DIR, uuid_name + 'trainData')
    testData_filepath = os.path.join(file_DIR, uuid_name + 'testData')
    trainData.write.format("csv").save(trainData_filepath)
    testData.write.format("csv").save(testData_filepath)
    trainData.show()
    testData.show()
    filepath1 = [trainData_filepath, testData_filepath]
    spark.stop()
    return filepath1


@app.task
def FillNa(FilePath, feature_columns, Fill):
    '''
    :param FilePath: 文件路径
    :param feature_columns: 特征变量 列号
    :param Fill: 缺失值填充方式
    :return: 返回字典 含文件路径
    '''
    msg = {'status': True, 'error': None, 'data': None}
    try:
        NAME = 'fillNA'
        CLASS = 'Data_Process'
        spark = SparkSession.builder.appName("myModel").getOrCreate()
        df = spark.read.csv(FilePath, inferSchema=True, encoding="gbk")
        # df.show()
        feature_colname = [df.columns[ii] for ii in feature_columns]
        if Fill == "mean":
            for i in feature_colname:
                means = df.agg(*[functions.mean(i).alias(i)]).toPandas().to_dict('records')[0].get(i)
                print(means,"121212")
                df = df.na.fill({i: means})
                df.show()
        elif Fill == "min":
            for i in feature_colname:
                mins = df.agg(*[functions.min(i).alias(i)]).toPandas().to_dict('records')[0].get(i)
                df = df.na.fill({i: mins})
        else:
            for i in feature_colname:
                maxs = df.agg(*[functions.max(i).alias(i)]).toPandas().to_dict('records')[0].get(i)
                df = df.na.fill({i: maxs})
        df.show()
        uuid_name = str(uuid.uuid1())
        FillData_filepath = os.path.join(filepath_DIR, uuid_name)
        df.write.csv(FillData_filepath)
        spark.stop()
        out_result = {}
        out_result["function_name"] = NAME
        out_result["function_class"] = CLASS
        out_result["filepath"] = FillData_filepath
        msg["data"] = out_result
    except Exception as e:
        msg["status"] = False
        msg["error"] = '执行失败：%s' % e
    msg = json.dumps(msg)
    return msg
