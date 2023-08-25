import logging

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app.authorization.serializers import DepartmentSerializer
from app.authorization.services.company_service import CompanyService


logger = logging.getLogger(__name__)


class DepartmentCreateView(APIView):
    # TODO: добавить права

    def post(self, request: Request, **kwargs):
        logger.debug('DepartmentCreateView | POST')
        serializer = DepartmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)
