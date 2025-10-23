from django.urls import path
from . import views

urlpatterns = [
    path('', views.Home, name='home'),
    path('api/classify/', views.classify_image, name='classify_image'),
    path('api/model-status/', views.get_model_status, name='model_status'),
]
