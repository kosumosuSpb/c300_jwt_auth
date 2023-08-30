import logging

from config.celery_app import app
from app.authorization.services.email_service import EmailService


logger = logging.getLogger(__name__)


@app.task
def send_activation_mail(user_id: str | int, address: str, code: str):
    """Отправка письма активации регистрации"""
    logger.debug('send_activate_email')
    email_service = EmailService()
    email_service.send_activation_email(user_id, address, code)
