# pyre-ignore-all-errors
from django.shortcuts import render # pyre-ignore
from image.models import Image, LikePost, CommentPost # pyre-ignore
# Create your views here.
from django.shortcuts import render # pyre-ignore
from generate.models import Permission # pyre-ignore
# Create your views here.
def add_index(request):

    return render(request,"temp/index.html")
from django.shortcuts import redirect # pyre-ignore

def add_index1(request):
    ss = request.session.get('u_id')
    if request.session.get('type') != 'user':
        return redirect('/login/login/')
    current_user = Register.objects.filter(register_id=ss).first() if ss else None
    return render(request,"temp/user_home.html", {'current_user': current_user})
    
def add_index2(request):
    if request.session.get('type') != 'admin':
        return redirect('/login/login/')
    return render(request,"temp/admin_home.html")
from register.models import Register, Follower # pyre-ignore
from django.db.models import Count # pyre-ignore

def get_feed_data(request):
    """Helper to fetch all data needed for the feed."""
    ss = request.session.get('u_id')
    # Cleanup logic temporarily disabled to prevent valid post deletion
    # existing_user_ids = Register.objects.values_list('register_id', flat=True)
    # Image.objects.exclude(register_id__in=existing_user_ids).delete()
    # Permission.objects.exclude(user_id__in=existing_user_ids).delete()
    # Permission.objects.exclude(image_id__in=Image.objects.values_list('image_id', flat=True)).delete()

    from django.db.models import Prefetch, Exists, OuterRef, Count, Q # pyre-ignore
    from image.models import LikePost, CommentPost # pyre-ignore
    from generate.models import Permission # pyre-ignore
    
    # Determine the current user's following list (users they follow)
    following_ids = list(Follower.objects.filter(follower_user_id=ss).values_list('user_id', flat=True))

    # Efficiently pre-fetch related tables in batch, avoiding N+1 synchronous loops
    # Limit to the 15 most recent posts for massive performance gains on dashboard load
    # Filter out posts from private accounts unless we follow them or own them
    posts_query = Image.objects.select_related('register').filter(
        (Q(register__is_private=False) | Q(register_id=int(ss)) | Q(register_id__in=following_ids)),
        is_story=False
    ).exclude(register__status='hibernated').prefetch_related(
        Prefetch('comments', queryset=CommentPost.objects.select_related('user').order_by('-created_at')),
        'likes',
        Prefetch('permission_set', queryset=Permission.objects.all()) # Cannot use select_related('user') here, user_id is just an IntegerField
    ).order_by('-image_id')[:30]
    
    posts = list(posts_query)

    # Pre-fetch all tagged registers in bulk to avoid an inner N+1 loop
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
        # Resolve tags in memory using the pre-fetched map and permission_set
        tag_names = []
        perms_status_hash = "" # To append cachebusters intelligently
        for p in post.permission_set.all():
            perms_status_hash += f"{p.user_id}{p.status}"
            if str(p.user_id) != str(post.register_id):
                first_name = tagged_users_map.get(int(p.user_id))
                if first_name:
                    tag_names.append(first_name)
                    
        post.tags = tag_names
        
        import hashlib # pyre-ignore
        # Creates a short 8-char hash of the exact permissions states
        post.perms_hash = hashlib.md5(perms_status_hash.encode()).hexdigest()[:8] # pyre-ignore
        
        post.like_count = post.likes.count() # Evaluated in memory thanks to prefetch_related
        
        # Check if current user liked it in memory
        post.has_liked = any(like.user_id == int(ss) for like in post.likes.all())
        
        # Fetch the top 3 comments from the pre-fetched QuerySet
        post.recent_comments = post.comments.all()[:3]
        
        # --- TURBO-FEED EXIF BYPASS ---
        # Instead of synchronously reading 50MB of images sequentially from the drive
        # we strictly load processed cached boxes generated during Upload or Notification layers.
        # This resolves the severe timeouts entirely.
        from django.core.cache import cache # pyre-ignore
        cache_key = f"feed_{post.image_id}_{post.perms_hash}"
        cached_blur = cache.get(cache_key)
        
        if cached_blur is not None:
            post.blur_boxes = cached_blur
        else:
            post.blur_boxes = [] # Failsafe zero-render if cache expires, user must click to view explicitly.
            
    return {
        'a': posts,
        'following_ids_list': following_ids
    }

def add_index3(request):
    ss = request.session.get('u_id')
    if not ss or request.session.get('type') != 'user':
        return redirect('/login/login/')
        
    current_user = Register.objects.filter(register_id=ss).first()
    if not current_user:
        return redirect('/login/login/')

    feed_data = get_feed_data(request)
    
    # Stats for the current user
    user_posts_count = Image.objects.filter(register_id=ss, is_story=False).count()
    
    # Actually fetch the lists of users so they can be viewed in the UI popup
    following_ids = list(Follower.objects.filter(follower_user_id=ss).values_list('user_id', flat=True))
    following_list = Register.objects.filter(register_id__in=following_ids).exclude(status='hibernated')
    following_count = following_list.count()
    
    follower_ids = list(Follower.objects.filter(user_id=ss).values_list('follower_user_id', flat=True))
    followers_list = Register.objects.filter(register_id__in=follower_ids).exclude(status='hibernated')
    followers_count = followers_list.count()
    
    suggestions = Register.objects.exclude(register_id=ss).exclude(register_id__in=following_ids).exclude(status='hibernated')[:5]
    from register.models import FollowRequest # pyre-ignore
    follow_req_count = FollowRequest.objects.filter(target_user_id=ss).count()
    notif_count = Permission.objects.filter(status='pending', user_id=ss).count() + follow_req_count
    
    # Calculate Mutual Friends for Stories Network
    following_ids_set = set(following_ids)
    followers_ids_set = set(follower_ids)
    mutual_friend_ids = following_ids_set.intersection(followers_ids_set)
    mutual_friend_ids.add(int(ss)) # Show own stories
    
    from datetime import datetime, timedelta # pyre-ignore
    current_time = datetime.now()
    
    # Fetch authentic Neon Silhouette Stories natively to process absolute physical temporal expirations
    raw_stories = Image.objects.select_related('register').filter(
        is_story=True, 
        register_id__in=mutual_friend_ids
    ).exclude(register__status='hibernated').order_by('-image_id')[:50]
    
    stories_dict = {}
    for s in raw_stories:
        try:
            s_dt = datetime.strptime(f"{s.date} {s.time}", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                s_dt = datetime.strptime(f"{s.date} {s.time}", "%Y-%m-%d %H:%M")
            except ValueError:
                continue
                
        if current_time - s_dt <= timedelta(hours=24):
            if s.register_id not in stories_dict:
                stories_dict[s.register_id] = s
            else:
                # Start playback from the oldest active story chronologically
                if s.image_id < stories_dict[s.register_id].image_id:
                    stories_dict[s.register_id] = s
                    
    stories = list(stories_dict.values())
    stories.sort(key=lambda x: x.image_id, reverse=True)  # Still sort latest active users first
    
    c = {
        'notif_count': notif_count,
        'current_user': current_user,
        'user_posts_count': user_posts_count,
        'followers_count': followers_count,
        'following_count': following_count,
        'followers_list': followers_list,
        'following_list': following_list,
        'suggestions': suggestions,
        'stories': stories,
    }
    if feed_data:
        c.update(feed_data)

    return render(request,"temp/dashboard.html",c)

def ajax_feed(request):
    """Returns only the feed items for AJAX polling."""
    data = get_feed_data(request)
    if data is None:
        return render(request, "temp/feed_partial.html", {'logout': True})
    return render(request, "temp/feed_partial.html", data)

def notification(request):

    ss = request.session.get('u_id')

    if not ss or request.session.get('type') != 'user':
        from django.shortcuts import redirect # pyre-ignore
        return redirect('/login/login/')

    obj = list(Permission.objects.filter(
        status='pending',
        user_id=ss
    ).select_related('image', 'image__register'))   # ✅ Fixed N+1 query issue

    # Fetch recent followers for notifications
    from register.models import Follower # pyre-ignore
    recent_followers = Follower.objects.filter(user_id=ss).select_related('follower_user').order_by('-follower_id')[:20]

    # --- OPTIMIZATION 1: Pre-fetch all approved permissions for these images to avoid N+1 DB queries ---
    image_ids = [perm.image_id for perm in obj if perm.image]
    approved_perms = Permission.objects.filter(image_id__in=image_ids, status='approved')
    approved_map = {}
    for ap in approved_perms:
        approved_map.setdefault(ap.image_id, set()).add(str(ap.user_id)) # pyre-ignore

    # --- CALCULATE ZERO-STORAGE CSS BLUR BOXES FOR NOTIFICATIONS ---
    import os, json, piexif, piexif.helper # pyre-ignore
    from PIL import Image as PILImage # pyre-ignore
    from django.conf import settings # pyre-ignore
    from django.core.cache import cache # pyre-ignore

    for perm in obj:
        if not perm.image or not perm.image.photo:
            continue
            
        authorized = {str(perm.image.register_id), str(ss)} # Uploader + The Viewer analyzing the tag
        
        blur_boxes = []
        filepath = os.path.join(settings.MEDIA_ROOT, perm.image.photo)
        
        # --- OPTIMIZATION 2: Cache EXIF Disk I/O Extraction ---
        cache_key = f"notif_exif_v2_{perm.image_id}"
        cached_exif = cache.get(cache_key)
        
        if cached_exif:
            img_w, img_h, json_coords = cached_exif
        else:
            img_w, img_h, json_coords = None, None, None
            if os.path.exists(filepath):
                try:
                    with PILImage.open(filepath) as img:
                        img_w, img_h = img.size
                        
                    exif_dict = piexif.load(filepath)
                    user_comment = exif_dict.get("Exif", {}).get(piexif.ExifIFD.UserComment)
                    if user_comment:
                        json_string = piexif.helper.UserComment.load(user_comment)
                        if json_string:
                            json_string = "".join(c for c in json_string if c.isprintable() and not c.isspace())
                            json_coords = json.loads(json_string)
                            # Cache EXIF geometry for 24 hours to skip expensive Disk Reads
                            cache.set(cache_key, (img_w, img_h, json_coords), timeout=86400)
                except Exception as e:
                    print(f"Failed EXIF CSS blur parsing in Notifs: {e}")
                    
        if json_coords and img_w and img_h:
            for face in json_coords:
                is_authorized = False
                
                # Check EXIF mapped user_id
                if face.get('user_id') and str(face.get('user_id')) in authorized:
                    is_authorized = True
                    
                # Check EXIF manual tag name
                if not is_authorized and face.get('name') and str(face.get('name')) == str(ss):
                    is_authorized = True
                    
                # Uploader is always visible!
                if not is_authorized and face.get('name') and str(face.get('name')) == str(perm.image.register_id):
                    is_authorized = True
                    
                if not is_authorized:
                    # Reverted to Perfect Square for Perfect CSS Circles
                    x, y, w, h = face['x'], face['y'], face['w'], face['h']
                    max_dim = max(w, h)
                    offset = max_dim * 0.4
                    
                    left_px = max(0, x - offset) # pyre-ignore
                    top_px = max(0, y - offset) # pyre-ignore
                    width_px = max_dim + (offset * 2)
                    height_px = max_dim + (offset * 2)
                    
                    if left_px + width_px > img_w: width_px = img_w - left_px # pyre-ignore
                    if top_px + height_px > img_h: height_px = img_h - top_px # pyre-ignore
                    
                    blur_boxes.append({
                        'left': f"{(left_px / img_w) * 100:.2f}%", # pyre-ignore
                        'top': f"{(top_px / img_h) * 100:.2f}%", # pyre-ignore
                        'width': f"{(width_px / img_w) * 100:.2f}%", # pyre-ignore
                        'height': f"{(height_px / img_h) * 100:.2f}%" # pyre-ignore
                    })
                
        perm.image.blur_boxes = blur_boxes

    from register.models import FollowRequest # pyre-ignore
    follow_requests = FollowRequest.objects.filter(target_user_id=ss).select_related('requester_user').order_by('-request_id')

    current_user = Register.objects.filter(register_id=ss).first() if ss else None
    context = {
        'u': obj,
        'followers': recent_followers,
        'follow_requests': follow_requests,
        'current_user': current_user
    }

    return render(request, "temp/notifications.html", context)

def explore_feed(request):
    ss = request.session.get('u_id')
    if not ss or request.session.get('type') != 'user':
        from django.shortcuts import redirect # pyre-ignore
        return redirect('/login/login/')

    current_user = Register.objects.filter(register_id=ss).first()
    
    # Exclude the current user so they aren't exploring themselves
    all_users = Register.objects.exclude(register_id=ss).exclude(status='hibernated')
    
    context = {
        'current_user': current_user,
        'all_users': all_users
    }
    return render(request, "temp/explore_feed.html", context)

def get_user_posts_json(request, user_id):
    from django.http import JsonResponse # pyre-ignore
    from image.models import Image # pyre-ignore
    
    # Fetch 5 latest posts from user
    posts = Image.objects.filter(register_id=user_id, is_story=False).order_by('-image_id')[:5]
    
    data = []
    for p in posts:
        data.append({
            'id': p.image_id,
            'url': f'/image/content/media/{p.image_id}/',
            'caption': p.caption or "Shared a moment secured by AssentTag protocol."
        })
        
    return JsonResponse({'posts': data})
