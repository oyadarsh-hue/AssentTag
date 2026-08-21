from django.urls import path
from . import views

urlpatterns = [
    path('view/',views.add_feedback),
    path('feedback/',views.add_feedback1)
]