from django.urls import path

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from app.authorization.views import RegisterView, TokenVerifyAuthView


# router = DefaultRouter(trailing_slash=True)
#
# router.register(r'register', RegisterView.as_view(), basename='register')
# router.register(r'login', TokenObtainPairView.as_view(), basename='token_obtain')
# router.register(r'login/refresh', TokenRefreshView.as_view(), basename='token_refresh')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('verify/', TokenVerifyAuthView.as_view(), name='token_verify'),
]
