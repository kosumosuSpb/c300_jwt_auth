from django.urls import path

from apps.authorization.views.company import DepartmentCreateView


urlpatterns = [
    path('departmentcreate/', DepartmentCreateView.as_view(), name='department_create'),
]
