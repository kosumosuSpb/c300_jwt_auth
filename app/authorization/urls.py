from django.urls import path

from app.authorization.views.account_views import (
    RegisterView,
    ActivateAccountView,
    TestView,
)
from app.authorization.views.auth_views import (
    LoginView,
    TokenRefreshCookieView,
    LogoutView,
)


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('login/refresh/', TokenRefreshCookieView.as_view(), name='token_refresh'),
    path('activate/', ActivateAccountView.as_view(), name='activate'),
    path('test/', TestView.as_view(), name='test'),

    # path('verify/', TokenVerifyAuthView.as_view(), name='token_verify'),
]

