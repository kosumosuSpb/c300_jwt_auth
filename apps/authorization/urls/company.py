from django.urls import path

from apps.authorization.views.company_views import DepartmentCreateView


urlpatterns = [
    path('departmentcreate/', DepartmentCreateView.as_view(), name='department_create'),
]
