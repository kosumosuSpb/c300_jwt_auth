from django.urls import path

from app.authorization.views import (
    RegisterView,
    TokenVerifyAuthView,
    LoginView,
    TokenRefreshCookieView,
    LogoutView,
    TestView,
)


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('login/refresh/', TokenRefreshCookieView.as_view(), name='token_refresh'),
    path('test/', TestView.as_view(), name='test'),
    # path('verify/', TokenVerifyAuthView.as_view(), name='token_verify'),
]

