from django.urls import path

from apps.authorization.views.auth import (
    LoginView,
    TokenRefreshCookieView,
    LogoutView,
    TokenVerifyAuthView
)


urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshCookieView.as_view(), name='token_refresh'),
    path('verify/', TokenVerifyAuthView.as_view(), name='token_verify'),
]
