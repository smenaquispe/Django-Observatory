"""URL configuration for Django Observatory"""
from django.urls import path
from . import views

app_name = 'django_observatory'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('request/<int:request_id>/', views.request_detail_view, name='request_detail'),
    path('api/requests/', views.api_requests_list, name='api_requests'),
]
