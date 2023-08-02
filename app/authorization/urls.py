from django.urls import path

from app.authorization.views import (
    RegisterView,
    TokenVerifyAuthView,
    LoginView,
    TokenRefreshCookieView
)


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('login/refresh/', TokenRefreshCookieView.as_view(), name='token_refresh'),
    # path('verify/', TokenVerifyAuthView.as_view(), name='token_verify'),
]
