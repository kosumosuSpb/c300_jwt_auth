from django.urls import path

from apps.authorization.views.permissions import (
    PermissionDetailView,
    PermissionListView
)


urlpatterns = [
    path('', PermissionListView.as_view(), name='permission_list'),
    path('create/', PermissionListView.as_view(), name='permission_create'),
    path('<str:name>/', PermissionDetailView.as_view(), name='permission_detail'),
]
