import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from apps.authorization.services.base_service import BaseService


logger = logging.getLogger(__name__)


class EmailService(BaseService):
    """Сервис для работы с почтой"""

    @staticmethod
    def send(to: str, subject: str, message: str, from_email=settings.DEFAULT_FROM_EMAIL):
        """Отправка почты"""
        msg = EmailMultiAlternatives(
            subject,
            message,
            from_email,
            [to])
        # msg.attach_alternative(html_content, "text/html")
        msg.send()

    @classmethod
    def send_activation_email(
            cls,
            user_id: str | int,
            to: str,
            code: str,
            from_email=settings.DEFAULT_FROM_EMAIL
    ):
        """Отправка письма активации с использованием шаблона"""
        logger.debug('send_activation_email')

        link = (f'http://localhost:8000/api/v1/activate/?'
                f'user_id={user_id}&'
                f'activation_code={code}')  # TODO: исправить на незахардкоженую ссылку

        subject = f'Ссылка для активации аккаунта {to}'
        html_content = f'<p>Пройдите по ссылке для активации вашего аккаунта: {link}</p>'
        text_content = f"Пройдите по ссылке для активации вашего аккаунта: {link}"

        msg = EmailMultiAlternatives(
            subject,
            text_content,
            from_email,
            [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        logger.debug('Письмо со ссылкой активации отправлено')
