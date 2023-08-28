from app.authorization.services.base_service import BaseService
from app.authorization.tasks import send_activate_email


class EmailService(BaseService):
    """Сервис для работы с почтой"""
    def __init__(self, host: str, login: str, password: str):
        self.host = host
        self.login = login
        self.password = password

    def send(self):
        """Отправка почты"""
        send_activate_email.delay()
