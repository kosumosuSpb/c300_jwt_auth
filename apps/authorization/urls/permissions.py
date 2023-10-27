from django.urls import path

from apps.authorization.views.permissions import (
    PermissionDetailView,
    PermissionListView
)


urlpatterns = [
    path('list/', PermissionListView.as_view(), name='permission_list'),
    path('detail/', PermissionDetailView.as_view(), name='permission_detail'),
]
