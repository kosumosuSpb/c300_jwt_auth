import os
import logging

from celery import Celery
import django


logger = logging.getLogger(__name__)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


app = Celery()
app.config_from_object('django.conf:settings', namespace='celery')


app.autodiscover_tasks()
