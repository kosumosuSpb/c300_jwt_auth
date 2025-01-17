import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authorization.serializers import DepartmentSerializer
from apps.authorization.services.company_service import CompanyService


logger = logging.getLogger(__name__)


class DepartmentCreateView(APIView):
    # TODO: добавить права
    @swagger_auto_schema(
        tags=['company'],
    )
    def post(self, request: Request, **kwargs):
        """Создание отдела компании"""
        logger.debug('DepartmentCreateView | POST | request.data: %s',
                     request.data)
        serializer = DepartmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        company = serializer.validated_data.get('company')
        company_service = CompanyService(company)
        company_service.create_department(**serializer.validated_data)

        return Response(data=serializer.data, status=status.HTTP_201_CREATED)
