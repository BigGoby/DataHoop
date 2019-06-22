# -*- coding: utf-8 -*-
import os
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
