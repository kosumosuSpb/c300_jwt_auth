import logging

from app.authorization.models.houses import HouseGroup, House
from app.authorization.models.area import Area
from app.authorization.models.company_profile import CompanyProfile
from app.authorization.models.tenant_profile import TenantProfile
from app.authorization.models.owner_area import OwnerArea


logger = logging.getLogger(__name__)


class HouseService:
    """Сервис по работе с группами домов, домами, и квартирами"""
    def __init__(
            self,
            house: House,
            house_group: HouseGroup | None = None,
            area: Area | None = None
    ):
        self.house_group = house_group
        self.house = house
        self.area = area

    @staticmethod
    def create_house(
            city: str,
            street: str,
            number: str,
            letter: str | None = None,
            provider=None,
            zip: str | None = None
    ) -> House:
        """
        Создание дома

        Args:
            zip: почтовый индекс
            city:  город
            street: улица
            number: номер дома
            letter: литера/дробь
            provider: компания-поставщик услуг

        Returns: Объект дома (модель)
        """
        house = House.objects.create(city, street, number, letter, provider=provider, zip=zip)
        logger.debug('Объект House создан: %s', house)
        return house

    @staticmethod
    def create_house_group(name: str, provider: CompanyProfile) -> HouseGroup:
        """
        Создаёт группу домов

        Args:
            name: Название группы домов
            provider: Обслуживающая организация

        Returns: HouseGroup
        """
        group = HouseGroup.objects.create(name, provider)
        logger.debug('Объект HouseGroup создан: %s', group)
        return group

    @staticmethod
    def create_area(number: int) -> Area:
        """Создание помещения"""
        area = Area.objects.create(number=number)
        logger.debug('Объект Area создан: %s', area)
        return area

    def link_house_area(self, house: House, area: Area):
        """Связывает дом и помещение"""

    def link_house_group_house(self, house_group: HouseGroup, house: House):
        """Связывает дом с группой домов"""
