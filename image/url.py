from django.urls import path
from . import views

urlpatterns = [
    path('image/',views.add_image1),
    path('view/',views.add_image),
    path('review-tag/<int:perm_id>/', views.review_tag),
    path('verify-live-face/<int:perm_id>/', views.verify_live_face),
    path('approve-tag/<int:perm_id>/', views.approve_tag),
    path('reject-tag/<int:perm_id>/', views.reject_tag),
    path('like-post/<int:image_id>/', views.like_post),
    path('add_comment/<int:image_id>/', views.add_comment),
    path('delete-comment/<int:comment_id>/', views.delete_comment),
    path('delete_post/<int:id>/', views.delete_post),
    path('add_text_post/', views.add_text_post),
    path('add_story/', views.add_story),
    path('view_story/<int:story_id>/', views.view_story),
    path('content/media/<int:image_id>/', views.serve_dynamic_image),
    path('content/notif/<int:image_id>/<int:target_id>/', views.serve_dynamic_notif),
    path('content/profile/<int:user_id>/', views.serve_profile_image),
    path('get_likers/<int:post_id>/', views.get_likers),
]