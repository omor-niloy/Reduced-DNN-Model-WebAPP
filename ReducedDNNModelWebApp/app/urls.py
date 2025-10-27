from django.urls import path
from . import views

urlpatterns = [
    path('', views.Home, name='home'),
    path('api/process-model/', views.process_model, name='process_model'),
    path('download/<str:filename>/', views.download_model, name='download_model'),
    path('api/view-architecture/<str:filename>/', views.view_architecture, name='view_architecture'),
]
