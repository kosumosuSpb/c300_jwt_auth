import os
import logging

from celery import Celery
import django


logger = logging.getLogger(__name__)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

app = Celery('celery_app')
app.config_from_object('django.conf:settings', namespace='CELERY')


app.autodiscover_tasks()
