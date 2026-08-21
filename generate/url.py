from django.urls import path
from generate import views

urlpatterns = [
      path('generate/',views.generate)
]