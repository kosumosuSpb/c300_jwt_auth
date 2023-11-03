from django.urls import path

from apps.authorization.views.permissions import (
    PermissionDetailView,
    PermissionListView,
    PermissionCreateOneView,
    # PermissionGrantView
)


urlpatterns = [
    path('', PermissionListView.as_view(), name='permissions'),
    path('create_one/', PermissionCreateOneView.as_view(), name='permission_create_one'),
    path('<str:name>/', PermissionDetailView.as_view(), name='permission_detail'),
    # path('user/<int:user_id>/', PermissionGrantView.as_view(), name='permission_grant'),
]
