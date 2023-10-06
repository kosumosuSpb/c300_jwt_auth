from django.urls import path

from apps.authorization.views.auth_views import (
    LoginView,
    TokenRefreshCookieView,
    LogoutView,
)


urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshCookieView.as_view(), name='token_refresh'),
]
