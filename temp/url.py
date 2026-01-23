from django.urls import path
from . import views

urlpatterns = [
    path('index/', views.add_index),
    path('index1/', views.add_index1),
    path('index2/', views.add_index2),
]
