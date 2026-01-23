from django.urls import path
from . import views

urlpatterns = [
path('image/',views.add_image1),
path('view/',views.add_image)
]