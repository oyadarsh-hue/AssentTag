from django.urls import path, re_path
from . import views

urlpatterns = [
    path('admin_view/', views.add_register),
    path('register/', views.add_register1),
    path('individual-user/',views.add_individual_users),
    path('profile/', views.user_profile),
    re_path(r'^edit/(?P<idd>\w+)/$', views.add_profile_edit),
    re_path(r'^u_view_profile/(?P<idd>\w+)/$', views.public_profile),
    re_path(r'^reject/(?P<idd>\w+)/$', views.reject),
    re_path(r'^accept/(?P<idd>\w+)/$', views.accept),
    path('scorched_earth/', views.scorched_earth),
    path('deactivate/', views.deactivate_account),
]
