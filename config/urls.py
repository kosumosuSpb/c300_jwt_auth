"""
URL configuration for c300_auth project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.contrib import admin
from django.urls import path
from django.conf.urls import include

from config.settings import (
    API_BASE_URL,
    DEBUG,
)
from config.swagger import urlpatterns as docs

# from apps.authorization.urls import router


urlpatterns = [
    # path('admin/', admin.site.urls),
    path(API_BASE_URL + 'auth/', include('apps.authorization.urls.auth')),
    path(API_BASE_URL + 'account/', include('apps.authorization.urls.account')),
    path(API_BASE_URL + 'company/', include('apps.authorization.urls.company')),
    path(API_BASE_URL + 'permissions/', include('apps.authorization.urls.permissions')),
]

if DEBUG:
    urlpatterns += docs
