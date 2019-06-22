import os
from django.conf import settings

# 项目根目录
BASEDIR = settings.BASE_DIR
# BASEDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 获取日志配置
import datetime
import logging
import sys


# 日志级别大小关系为：CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
def log(modelName, log_fn=None, consoles='yes', mode=None, level=logging.DEBUG, \
        format='%(levelname)s - %(asctime)s - %(name)s [line:%(lineno)d] - %(message)s'):
    '''
    simplest basicConfig wrapper, open log file and return default log handler
    '''

    if log_fn is None:
        now = datetime.datetime.now()
        ts = now.strftime('%Y-%m-%d')
        log_fn = '%s/logs/%s.log' % (BASEDIR, ts)

    if mode is None:
        mode = 'a+'

    logging.basicConfig(level=level,
                        format=format,
                        filename=log_fn,
                        filemode=mode)
    #################################################################################################
    # 定义一个StreamHandler，将INFO级别或更高的日志信息打印到标准错误，并将其添加到当前的日志处理对象#
    if consoles != None:
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(name)-12s-%(levelname)s-: %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)
    #################################################################################################
    logger = logging.getLogger(modelName)
    if mode.lower() == 'w':
        logger.info('---=== START ===---')

    return logger


if __name__ == '__main__':
    log = log(__name__)
    log.info('message')
    log.fatal('exit')
    log.error('asdfasdf')
'''
# 加载日志模块
from utils.logConf import log
logger = log(__name__)

'''
