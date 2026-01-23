from django.urls import path, re_path
from . import views

urlpatterns = [
    path('admin_view/', views.add_register),
    path('register/', views.add_register1),

    re_path(r'^accept/(?P<idd>\w+)/$', views.accept),
    re_path(r'^reject/(?P<idd>\w+)/$', views.reject),
]
