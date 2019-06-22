# coding: utf-8

from celery import Celery
from django.conf import settings

app = Celery('tasks',
             broker=settings.RABBITMQ_HOST,
             backend=settings.RABBITMQ_HOST,
             include=['demoCelery.tasks'])
app.config_from_object('demoCelery.config')

if __name__ == '__main__':
    app.start()
