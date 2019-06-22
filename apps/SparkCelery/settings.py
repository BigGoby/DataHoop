# -*- coding: utf-8 -*-
import os
#项目根目录
BASEDIR = os.path.join((os.path.dirname(os.path.abspath(__file__))))
url = "hdfs://master:9000/datahoop/"
filepath_DIR = "hdfs://master:9000/datahoop/"                  #文件路径
filepath_model_DIR = "hdfs://master:9000/datahoop/filepath_model/"       #模型路径
filepath_result_DIR = "hdfs://master:9000/datahoop/filepath_result/"   #拟合或预测结果
# mongo地址
mongodbUri = 'mongodb://172.17.0.100:27017'

#获取日志配置
import datetime
import logging
import sys
#日志级别大小关系为：CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
def quick_start_log(modelName,log_fn=None,consoles='yes', mode=None, level=logging.DEBUG,\
                    format='%(asctime)s - %(name)s [line:%(lineno)d] - %(levelname)s - %(message)s'):
    '''
    simplest basicConfig wrapper, open log file and return default log handler
    '''

    if log_fn is None:
        now = datetime.datetime.now()
        ts = now.strftime('%Y-%m-%d')
        log_fn = '%s/log/DT-%s.log' %(BASEDIR,ts)

    if mode is None:
        mode = 'a+'

    logging.basicConfig(level=level,
                        format=format,
                        filename=log_fn,
                        filemode=mode)
    logger = logging.getLogger(modelName)
    if mode.lower() == 'w':
        logger.info('---=== START ===---')

    return logger

if __name__ == '__main__':
    print(BASEDIR)
