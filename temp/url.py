from django.urls import path
from . import views

urlpatterns = [
    path('index/', views.add_index),
    path('index1/', views.add_index1),
    path('index2/', views.add_index2),
    path('index3/',views.add_index3),
    path('index4/',views.notification),
    path('explore/', views.explore_feed, name='explore_feed'),
    path('ajax_user_posts/<int:user_id>/', views.get_user_posts_json, name='ajax_user_posts'),
    path('ajax_feed/', views.ajax_feed, name='ajax_feed'),
]
