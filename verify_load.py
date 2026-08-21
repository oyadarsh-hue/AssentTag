import os
import sys
import django
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')
django.setup()

from register.models import Register, Follower
from image.models import Image, LikePost, CommentPost
from generate.models import Permission
from django.db.models import Prefetch

def test_optimized_feed():
    start_time = time.time()
    
    # Mock request session
    ss = '2' # Neo
    
    print("Testing optimized query...")
    posts_query = Image.objects.select_related('register').prefetch_related(
        Prefetch('comments', queryset=CommentPost.objects.select_related('user').order_by('-created_at')),
        'likes',
        Prefetch('permission_set', queryset=Permission.objects.all()) 
    ).order_by('-image_id')
    
    posts = list(posts_query)
    following_ids = list(Follower.objects.filter(follower_user_id=ss).values_list('user_id', flat=True))

    all_permission_user_ids = set()
    for post in posts:
        for p in post.permission_set.all():
            if str(p.user_id) != str(post.register_id):
                all_permission_user_ids.add(p.user_id)
                
    tagged_users_map = {
        user.register_id: user.first_name 
        for user in Register.objects.filter(register_id__in=all_permission_user_ids)
    }

    for post in posts:
        tag_names = []
        for p in post.permission_set.all():
            if str(p.user_id) != str(post.register_id):
                first_name = tagged_users_map.get(int(p.user_id))
                if first_name:
                    tag_names.append(first_name)
                    
        post.tags = tag_names
        post.like_count = post.likes.count() # Evaluated in memory thanks to prefetch_related
        post.has_liked = any(like.user_id == int(ss) for like in post.likes.all())
        post.recent_comments = post.comments.all()[:3]
        
    end_time = time.time()
    print(f"Data retrieved successfully. Found {len(posts)} posts.")
    print(f"Total query execution time: {(end_time - start_time) * 1000:.2f} ms")

if __name__ == "__main__":
    test_optimized_feed()
