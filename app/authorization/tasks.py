import logging

from config.celery_app import app


logger = logging.getLogger(__name__)


@app.task
def send_activate_email():
    """Отправка письма активации регистрации"""
    logger.debug('send_activate_email')
