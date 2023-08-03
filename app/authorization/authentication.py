import logging

from django.contrib.auth import get_user_model
from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import CSRFCheck


logger = logging.getLogger(__name__)


def enforce_csrf(request):
    """
    Enforce CSRF validation.
    """
    logger.debug('enforce_csrf | cookies: %s', request.COOKIES)
    check = CSRFCheck(request)
    # populates request.META['CSRF_COOKIE'], which is used in process_view()
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        # CSRF failed, bail with explicit error message
        logger.error('CSRF Failed: %s', reason)
        raise exceptions.PermissionDenied('CSRF Failed: %s' % reason)


class CookiesJWTAuthentication(JWTAuthentication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_model = get_user_model()

    def authenticate(self, request):
        logger.debug('CookiesJWTAuthentication | authenticate')

        # logger.debug('COOKIES: %s', request.COOKIES)
        # logger.debug('META: %s', request.META)

        if request.COOKIES:
            enforce_csrf(request)

        access_token = request.COOKIES.get('access_token')
        refresh = request.COOKIES.get('refresh_token')
        logger.debug('access: %s, refresh: %s', access_token, refresh)

        if access_token is None:
            logger.debug('access is None')
            return None

        validated_token = self.get_validated_token(access_token)
        user = self.get_user(validated_token)
        logger.debug('user: %s, validated_token: %s', user, validated_token)

        return user, validated_token
