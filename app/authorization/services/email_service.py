from app.authorization.services.base_service import BaseService


class EmailService(BaseService):
    """Сервис для работы с почтой"""
    def __init__(self, host: str, login: str, password: str):
        self.host = host
        self.login = login
        self.password = password

    def send(self):
        """Отправка почты"""
