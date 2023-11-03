from django.urls import path

from apps.authorization.views.account import (
    RegisterView,
    ActivateAccountView,
    UserProfileDetailView,
    UserDeleteView,
    TestView,
)


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/', ActivateAccountView.as_view(), name='activate'),
    path('delete/<int:user_id>/', UserDeleteView.as_view(), name='delete'),
    path('profile/<int:user_id>/', UserProfileDetailView.as_view(), name='profile'),
    path('test/', TestView.as_view(), name='test'),
]
