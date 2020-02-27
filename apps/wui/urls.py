"""Metis URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, re_path, include
import wui.views as views

app_name = 'wui'
urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^image$', views.list_image, name='list_image'),
    re_path(r'^image/new$', views.new_image, name='new_image'),
    re_path(r'^image/(?P<id>\d+)$', views.edit_image, name='edit_image'),
    re_path(r'^image/(?P<image_id>\d+)/bbox/new$', views.edit_bbox_image, name='new_bbox_image'),
    re_path(r'^image/(?P<image_id>\d+)/bbox/(?P<bbox_id>\d+)$', views.edit_bbox_image, name='edit_bbox_image'),
]
