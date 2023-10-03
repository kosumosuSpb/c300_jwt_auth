from django.urls import path

from apps.authorization.views.account_views import (
    RegisterView,
    ActivateAccountView,
    TestView,
)
from apps.authorization.views.auth_views import (
    LoginView,
    TokenRefreshCookieView,
    LogoutView,
)
from apps.authorization.views.company_views import DepartmentCreateView


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('login/refresh/', TokenRefreshCookieView.as_view(), name='token_refresh'),
    path('activate/', ActivateAccountView.as_view(), name='activate'),
    path('test/', TestView.as_view(), name='test'),
    path('departmentcreate/', DepartmentCreateView.as_view(), name='department_create'),

    # path('verify/', TokenVerifyAuthView.as_view(), name='token_verify'),
]
