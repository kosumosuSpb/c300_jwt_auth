from django.core.mail import EmailMultiAlternatives
from django.core.signing import Signer

from app.authorization.services.base_service import BaseService
from config.settings import EMAIL_FROM


class EmailService(BaseService):
    """Сервис для работы с почтой"""

    @staticmethod
    def send(to: str, subject: str, message: str, from_email=EMAIL_FROM):
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
            from_email=EMAIL_FROM
    ):
        """Отправка письма активации с использованием шаблона"""
        text_content = "Пройдите по ссылке для активации вашего аккаунта"
        activation_code = cls.make_activation_code(to)
        link = (f'http://localhost:8000/api/v1/activate/'
                f'user_id={user_id}&'
                f'activation_code={activation_code}')  # TODO: исправить на незахардкоженую ссылку
        html_content = f'<p>Пройдите по ссылке для активации вашего аккаунта: {link}</p>'
        subject = 'Ссылка для активации аккаунта'

        msg = EmailMultiAlternatives(
            subject,
            text_content,
            from_email,
            [to])
        msg.attach_alternative(html_content, "text/html")
        msg.content_subtype = "html"
        msg.send()

    @staticmethod
    def make_activation_code(string: str) -> str:
        """Создание кода активации"""
        signer = Signer()
        signed_value = signer.sign(string)

        return signed_value


