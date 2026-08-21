from django.urls import path
from varify import views

urlpatterns = [
      path('verify/',views.varify)
]