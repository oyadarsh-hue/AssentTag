from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.add_login),
    path('follow/<int:user_id>/', views.follow_user),
    path('unfollow/<int:user_id>/', views.unfollow_user),
    path('remove_follower/<int:user_id>/', views.remove_follower),
    path('accept_follow/<int:req_id>/', views.accept_follow),
    path('reject_follow/<int:req_id>/', views.reject_follow),
    path('chat/<int:user_id>/', views.chat_user),
    path('messages/', views.messages_inbox),
    path('financial_otp_verify/', views.financial_otp_verify),
    path('read_disappearing/<int:message_id>/', views.read_disappearing_message),
]