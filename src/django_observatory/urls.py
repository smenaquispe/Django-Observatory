"""URL configuration for Django Observatory"""
from django.urls import path
from . import views

app_name = 'django_observatory'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
]
