from django.urls import path,re_path
from . import views

urlpatterns = [
    path('view/', views.add_complaint_view),
    path('complaint/', views.add_complaint1),
    # path('reply/', views.add_reply),
    re_path('reply/(?P<idd>\w+)', views.add_reply),
]
