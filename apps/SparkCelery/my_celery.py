# coding: utf-8

from celery import Celery
from django.conf import settings
app = Celery('tasks',
             broker=settings.RABBITMQ_SPARK_HOST,
             backend=settings.RABBITMQ_SPARK_HOST,
             include=['SparkCelery.tasks'])
app.config_from_object('SparkCelery.config')

if __name__ == '__main__':
    app.start()


