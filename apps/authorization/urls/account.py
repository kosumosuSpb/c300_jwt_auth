from django.urls import path

from apps.authorization.views.account import (
    RegisterView,
    ActivateAccountView,
    UserDeleteView,
    TestView,
)


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/', ActivateAccountView.as_view(), name='activate'),
    path('delete/', UserDeleteView.as_view(), name='delete'),
    path('test/', TestView.as_view(), name='test'),
]
