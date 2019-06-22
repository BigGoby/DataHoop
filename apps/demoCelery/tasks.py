# coding: utf-8
# 59f03100b66db239f761f92f
# test_decision_boundary_fig
from .my_celery import app


@app.task
def add(x):
    print('11')


@app.task
def KNN_func(obj_id, sheet, Indx, Indy, n_neighbors, weights, p, test_size, random_state):
    """

    :param obj_id: obj_id
    :param sheet:  如果excel有sheet   excel sheet name
    :param Indx:   自变量
    :param Indy:   因变量
    :param n_neighbors:
    :param weights:
    :param p:
    :param test_size:
    :param random_state:
    :return:
    """
    print("KNN_func")


@app.task
def GaussianNB_func(obj_id, sheet, Indx, Indy, test_size, random_state):
    """

    :param obj_id:
    :param sheet:
    :param Indx:
    :param Indy:
    :param test_size:
    :param random_state:
    :return:
    """
    print("GaussianNB_func")


@app.task
def GBDT_func(obj_id, sheet, Indx, Indy, n_estimators, learning_rate, max_depth, test_size, random_state):
    # '59eee27db6cb5561c85c0fb2', 'Sheet1', '0,1,2,3', '4', 100,0.1,3 ,0.3, 0
    print("GBDT_func")


@app.task
def DecisionTree(obj_id, sheet, Indx, Indy, criterion, max_depth, test_size, random_state):
    """

    :param obj_id:
    :param sheet:
    :param Indx:
    :param Indy:
    :param criterion:
    :param max_depth:
    :param test_size:
    :param random_state:
    :return:
    """
    print("DecisionTree")
    # '59e997f4ff48350874c7e42a','','0,1,2,3', '4','gini',3, 0.5, 1


# 逻辑回归
@app.task
def LogisticRegression_func(obj_id, sheet, Indx, Indy, max_iter, solver, test_size, random_state):
    """
    :param obj_id:
    :param sheet:
    :param Indx:
    :param Indy:
    :param max_iter:
    :param solver:
    :param test_size:
    :param random_state:
    :return:
    """
    pass


# Adaboost
@app.task
def Adaboost_func(obj_id, sheet, Indx, Indy, n_estimators, learning_rate, test_size, random_state):
    pass


# 随机森林
# 分类树个数n_estimators、分类树损失函数criterion、树最大深度max_depth、测试集占整个数据集的比例test_size 伪随机数发生器种子random_state
@app.task
def RandomForest(obj_id, sheet, Indx, Indy, n_estimators, criterion, max_depth, test_size, random_state):
    """

    :param obj_id:
    :param sheet:
    :param Indx:
    :param Indy:
    :param n_estimators:
    :param criterion:
    :param max_depth:
    :param test_size:
    :param random_state:
    :return:
    """
    pass


@app.task
def SVM(obj_id, sheet, Indx, Indy, C, kernel, coef0, degree, gamma, max_iter, test_size, random_state):
    pass


# 神经网络
@app.task
def NeuralNetwork(obj_id, sheet, Indx, Indy, Hideen_layer_structure, activation, solver, alpha, learning_rate, max_iter,
                  momentum, early_stopping, validation_fraction, test_size, random_state):
    print("NeuralNetwork123")


# 预处理
@app.task
def Predict(obj_id, sheet_pred, Indx_pred, output):
    # 59f02a94b66db239eb61f92f
    # '59e997f4ff48350874c7e42a','','0,1,2,3','59f02a94b66db239eb61f92f'
    # '59eee27db6cb5561c85c0fb2', 'Sheet1', '2', '59f03100b66db239f761f92f'
    print("Predict")


@app.task
def Scaler(obj_id, sheet_pred, Indx_pred, output):
    print("Scaler")


################ 无监督学习 ############################################################
@app.task
def KMeans(obj_id, sheet_pred, x, cluster, init, iter_):
    # 59f8450dff48351d3c378b43
    print("KMeans")


@app.task
def KMedians(obj_id, sheet, Ind, cluster, metric_, iter_):
    # ['59e997dbff48351720dff356', '', '1,2',3,'euclidean',100]
    print("KMedians")


# 层次聚类
@app.task
def Hcluster_func(obj_id, sheet, Indx, metric, method):
    pass


# 关联分析-无监督学习
@app.task
def Apriori_func(obj_id, sheet, Ind, support, metric_, threshold):
    # '59e997dbff48351720dff350', '', '10,11,12,13,14,15', 0.02, 'confidence', 0.02
    print(Apriori_func)


# 对应分析-无监督学习
@app.task
def CorrespondenceAnalysis_func(obj_id, sheet, Ind):
    # '59e997dbff48351720dff35f','','0,1'
    print(CorrespondenceAnalysis_func)


# 线性回归
@app.task
def LinearRegression_func(obj_id, sheet, Indx, Indy):
    pass


############# 时间序列 ##############
# 季节分解预测
# Ind：x列号
# period：周期长度
# model_:模型模式（下拉选择，‘additive’，‘multiplicative’）
# forecast_:预测长度
@app.task
def seasonal_decomposition(obj_id, sheet, Indx, mtype, freq, forecast_):
    pass


# 简单指数平滑
@app.task
def ExponentialSmoothing_func(obj_id, sheet, Ind, forecast_):
    pass


# Holt指数平滑
# Ind:x列号
# forecast:预测长度(>0)
@app.task
def Holt_ExponentialSmoothing_func(obj_id, sheet, Ind, forecast):
    pass


# Winter指数平滑
# Ind:x列号
# period:周期长度
# model_:模型模式（下拉框，‘additive’，‘multiplicative’）
# forecast：预测长度
@app.task
def Winter_ExponentialSmoothing_func(obj_id, sheet, Ind, period, model_, forecast_):
    pass


# 移动平均
@app.task
def MovingAverage_func(obj_id, sheet, Ind, window_, center_):
    '''
    #移动平均
    :param obj_id:
    :param sheet:
    :param Ind: x列号
    :param window_: 移动窗口大小（大于0）
    :param center_: 是否在窗口中心（下拉菜单选择'True','False')
    :return:
    '''
    print("移动平均")


############# 词频分析 ##########################################
@app.task
def Word_Frequency_func(obj_id, sheet, Indx):
    print('词频')


@app.task
def text_rank_func(obj_id, sheet, Ind, num_keywords):
    print("TextRank")


############# 数据预处理 ###############################################
# 相关矩阵
@app.task
def CorrelationMatrix_func(obj_id, sheet, Ind):
    # '59e997dbff48351720dff358','','0,1'sssssssss
    print(CorrelationMatrix_func)


# 因子分析
@app.task
def FactorAnalysis(obj_id, sheet, Ind, select, subselect):
    print(FactorAnalysis)


# 异常值处理
@app.task
def OutliersProcessing_func(obj_id, sheet, Ind, method):
    # '59e997dbff48351720dff34e','','0,1,2,3,4,5,6,7,8,9','delete_row'
    print(OutliersProcessing_func)


# 主成分分析
@app.task
def PCA_func(obj_id, sheet, Ind, n_components):
    # '59e997dbff48351720dff365','','1,2,3,4,5',3
    print(PCA_func)


# LabelEncoder标签特征编码
@app.task
def Label_Encoder(obj_id, sheet, Ind):
    pass


# 多项式特征
@app.task
def Polynomial_Features_func(obj_id, sheet, Ind):
    pass


# OneHotEncoder独热编码
@app.task
def One_Hot_Encoder(obj_id, sheet, Ind):
    pass


# 变量离散化
@app.task
def Discretization_func(obj_id, sheet, Ind, k):
    pass


# Scaler
@app.task
def Scaler_func(obj_id, sheet, Ind, Args_Scaler, threshold):
    # '59e997dbff48351720dff354','','1,2', 'None', '1'
    print('Scaler_func')


############################-可视化-############################################

# 聚合函数
@app.task
def agg_func(obj_id="5a94b599ad5bfb362c880800", sheet="abc", dim=["地区", "城市", "年份"],
             value_agg=[["GDP（亿元）", "sum"], ["GDP第一产业（亿元）", "max"], ["GDP第二产业（亿元）", "min"]]):
    print('agg_func')
