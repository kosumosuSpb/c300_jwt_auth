import os
import logging

from celery import Celery
from celery.schedules import crontab
import django

logger = logging.getLogger(__name__)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery('celery_app')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    # Executes every day 3:00 a.m.
    'every_day_delete_expired_tokens_from_db': {
        'task': 'apps.authorization.tasks.delete_expired_tokens_from_db',
        'schedule': crontab(hour=3, minute=0),
        # 'args': (),
    },
    # 'test-every-5-seconds': {
    #     'task': 'celery_app.test_task',
    #     'schedule': 5.0,
    #     'args': (16, 16)
    # },
}


app.autodiscover_tasks()
