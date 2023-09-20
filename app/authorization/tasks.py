import datetime as dt
import logging

from django.db.models.query import QuerySet
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.utils import aware_utcnow

from config.celery_app import app
from app.authorization.services.email_service import EmailService


logger = logging.getLogger(__name__)


@app.task
def send_activation_mail(user_id: str | int, address: str, code: str):
    """Отправка письма активации регистрации"""
    logger.debug('send_activate_email')
    email_service = EmailService()
    email_service.send_activation_email(user_id, address, code)


def _delete_expired_outstanding_tokens_from_db():
    """
    Этот процесс можно запускать вручную командой
    python manage.py flushexpiredtokens
    """
    now = aware_utcnow()
    outstanding_tokens: QuerySet = OutstandingToken.objects.filter(expires_at__lte=now)
    outstanding_tokens.delete()


@app.task
def delete_expired_tokens_from_db():
    """Удаляет из БД рефреш токены с истёкшим сроком актуальности"""
    logger.debug('start delete_expired_tokens_from_db')
    _delete_expired_outstanding_tokens_from_db()
