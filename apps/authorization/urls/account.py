from django.urls import path

from apps.authorization.views.account import (
    RegisterView,
    ActivateAccountView,
    TestView,
)


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/', ActivateAccountView.as_view(), name='activate'),
    path('test/', TestView.as_view(), name='test'),
]
