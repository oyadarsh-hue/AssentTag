from django.shortcuts import render, redirect # pyre-ignore
from django.contrib import messages as notices
from register.models import  Register # pyre-ignore
from login.models import Login # pyre-ignore
from django.core.files.storage import FileSystemStorage # pyre-ignore
from django.core.files.base import ContentFile # pyre-ignore
import datetime # pyre-ignore
import base64 # pyre-ignore
import os # pyre-ignore
from assentag import settings # pyre-ignore
from face_utils import get_face_descriptor, compare_faces # pyre-ignore

def add_register1(request):
    if request.method == 'POST':
        obj=Register()
        obj.date = datetime.datetime.today()
        obj.time = datetime.datetime.now()
        obj.first_name=request.POST.get('fname')
        obj.last_name=request.POST.get('lname')
        obj.email=request.POST.get('email')
        obj.date_of_birth=request.POST.get('dob')
        obj.gender=request.POST.get('gender')
        obj.city=request.POST.get('city')
        obj.country=request.POST.get('country')
        obj.mobile=request.POST.get('mobile')
        obj.bio=request.POST.get('bio')
        
        password = request.POST.get('pass')
        confirm_password = request.POST.get('cpass')
        
        if password != confirm_password:
            return render(request, "register/register.html", {'msg': 'Error: Password and Confirm Password do not match.', 'msg_type': 'error'})
            
        import re # pyre-ignore
        if len(password) < 8 or not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password) or not re.search(r"[0-9]", password) or not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return render(request, "register/register.html", {'msg': 'Error: Password must be at least 8 characters and include uppercase, lowercase, number, and special character.', 'msg_type': 'error'})
            
        obj.password = password
        obj.confirm_password = confirm_password
        obj.status='pending'
        my_file = request.FILES['photo']
        fs = FileSystemStorage()
        import time # pyre-ignore
        
        # Create a clean unique filename to avoid overwriting previous generic filenames (e.g. image.jpg)
        ext = os.path.splitext(my_file.name)[1].lower()
        clean_name = f"reg_photo_{int(time.time()*1000)}{ext}"
        
        live_photo_data = request.POST.get('live_photo')
        
        # --- 3-Condition Validation Flow (Pure RAM Buffer) ---
        import numpy as np # pyre-ignore
        
        # Prepare Static Upload Descriptor in RAM completely before writing to disk
        file_bytes = my_file.read()
        static_desc = get_face_descriptor(file_bytes)
        
        # Prepare Live Capture Descriptor
        live_desc = None
        if live_photo_data:
            import cv2 # pyre-ignore
            import numpy as np # pyre-ignore
            from face_utils import detector, predictor, face_rec_model # pyre-ignore
            
            try:
                format, imgstr = live_photo_data.split(';base64,') 
                img_bytes = base64.b64decode(imgstr)
                np_arr = np.frombuffer(img_bytes, np.uint8)
                live_frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                live_rgb = cv2.cvtColor(live_frame, cv2.COLOR_BGR2RGB)
                
                # --- SAVE TO WINDOWS DESKTOP ---
                try:
                    import time
                    desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
                    desktop_save_path = os.path.join(desktop_dir, f"live_register_face_{int(time.time())}.jpg")
                    cv2.imwrite(desktop_save_path, live_frame)
                    print(f"[DEBUG] Saved live register face to desktop: {desktop_save_path}")
                except Exception as e:
                    print(f"Failed to save live register face to desktop: {e}")
                
                live_faces = detector(live_rgb)
                if len(live_faces) > 0:
                    largest_face = max(live_faces, key=lambda rect: rect.width() * rect.height())
                    shape = predictor(live_rgb, largest_face)
                    live_desc = np.array(face_rec_model.compute_face_descriptor(live_rgb, shape))
            except Exception as e:
                print(f"Error computing live face descriptor: {e}")
            
        if static_desc is None or live_desc is None:
            context = {'msg': 'Error: Biometric verification failed. Could not detect a clear face in BOTH photos.', 'msg_type': 'error'}
            return render(request, "register/register.html", context)
            
        # CONDITION 1: Live Face matches Uploaded Face
        dist_live_static = np.linalg.norm(static_desc - live_desc) # pyre-ignore
        if dist_live_static > 0.60: # Aligned with implementation specification
            context = {'msg': 'Registration Rejected: Fake Account. Live Face and Uploaded Photo do not match.', 'msg_type': 'error'}
            return render(request, "register/register.html", context)
            
        # CONDITION 2: Duplicate Account Check (Match directly against users' first-time registration photos in Static folder)
        known_faces = []
        static_dir = os.path.join(settings.BASE_DIR, 'static')
        
        for existing_user in Register.objects.all():
            anchor = getattr(existing_user, 'reg_photo', None) or getattr(existing_user, 'photo', None)
            if anchor:
                # Resolve the photo path inside the static directory
                file_path = os.path.join(static_dir, str(anchor))
                if os.path.exists(file_path):
                    # Compute the descriptor for the existing user's face to verify uniqueness
                    desc = get_face_descriptor(file_path)
                    if desc is not None:
                        known_faces.append((existing_user.register_id, desc))
                        
        # Tightened Threshold to 0.45 to permit Siblings/Twins. 0.60 is too broad for identical genetics.
        match_live_name, match_live_dist = compare_faces(known_faces, live_desc, threshold=0.45) 
        match_static_name, match_static_dist = compare_faces(known_faces, static_desc, threshold=0.45) 
        
        if match_live_name != "Unknown":
            context = {'msg': 'Registration Rejected: Duplicate Account. This Live Face is already registered.', 'msg_type': 'error'}
            return render(request, "register/register.html", context)
            
        if match_static_name != "Unknown":
            context = {'msg': 'Registration Rejected: Duplicate Account. This Uploaded Photo is already registered.', 'msg_type': 'error'}
            return render(request, "register/register.html", context)
        my_file.seek(0)
        saved_filename = fs.save(clean_name, my_file)
        obj.photo = saved_filename
        obj.reg_photo = saved_filename
        obj.save()

        ob = Login()
        ob.username = obj.email
        ob.password = obj.password
        ob.type = "user"
        ob.u_id = obj.register_id
        ob.save()
        
        notices.success(request, 'Your account was created successfully. You can now log in.', extra_tags='registration')
        return redirect('/login/login/')

    return render(request, "register/register.html")
def add_register(request):
    ob = Register.objects.all()
    context = {
        'b': ob
    }
    return render(request,"register/admin_users.html",context)

def accept(request, idd):
    from django.shortcuts import redirect # pyre-ignore
    j=Register.objects.get(register_id=idd)
    j.status='approved'
    j.save()
    return redirect('/register/individual-user/')

def user_profile(request):
    from django.shortcuts import redirect # pyre-ignore
    ss = request.session.get("u_id")
    if ss:
        j = Register.objects.get(register_id=ss)
        from image.models import Image # pyre-ignore
        user_posts = Image.objects.filter(register_id=ss, is_story=False).order_of_magnitude_fix = True # Just a marker
        user_posts = Image.objects.filter(register_id=ss, is_story=False).order_by('-image_id')
        return render(request, 'register/u_view_profile.html', {
            'j': j, 
            'current_user': j,
            'user_posts': user_posts
        })
    return redirect('/login/login/')

def public_profile(request, idd):
    ss = request.session.get('u_id')
    from django.shortcuts import redirect # pyre-ignore
    if not ss or request.session.get('type') != 'user':
        return redirect('/login/login/')
        
    j = Register.objects.filter(register_id=idd).first()
    if not j:
        return redirect('/index/index3/')
        
    current_user = Register.objects.filter(register_id=ss).first()
    
    from image.models import Image # pyre-ignore
    user_posts = Image.objects.filter(register_id=idd, is_story=False).order_by('-image_id')
    posts_count = user_posts.count()
    
    from register.models import Follower # pyre-ignore
    followers = Follower.objects.filter(user_id=idd).select_related('follower_user')
    following = Follower.objects.filter(follower_user_id=idd).select_related('user')
    
    followers_count = followers.count()
    following_count = following.count()
    
    is_following = Follower.objects.filter(follower_user_id=ss, user_id=idd).exists()
    
    from register.models import FollowRequest # pyre-ignore
    has_requested = FollowRequest.objects.filter(requester_user_id=ss, target_user_id=idd).exists()
    
    can_view_posts = True
    if j.is_private and str(ss) != str(idd):
        if not is_following:
            can_view_posts = False

    return render(request, 'register/public_profile.html', {
        'j': j,
        'current_user': current_user,
        'posts_count': posts_count,
        'followers_count': followers_count,
        'following_count': following_count,
        'followers': followers,
        'following': following,
        'is_following': is_following,
        'has_requested': has_requested,
        'user_posts': user_posts if can_view_posts else [],
        'can_view_posts': can_view_posts
    })

def reject(request,idd):
    from django.shortcuts import redirect # pyre-ignore
    obj=Register.objects.get(register_id=idd)
    obj.status='rejected'
    obj.save()
    return redirect('/register/individual-user/')
def add_individual_users(request):
    ss = request.session.get('u_id')
    ob = Register.objects.all()
    current_user = Register.objects.filter(register_id=ss).first() if ss else None
    context = {
        'k': ob,
        'current_user': current_user
    }
    return render(request,"register/individual-users.html",context)
def add_profile_edit(request, idd):
    import time # pyre-ignore
    ob = Register.objects.get(register_id=idd)
    ss = request.session.get('u_id', idd)
    current_user = Register.objects.filter(register_id=ss).first()
    # Give the template direct access to the current epoch time for cache busting
    context = {
        'j': ob,
        'current_time': int(time.time()),
        'current_user': current_user
    }
    if request.method == 'POST':
        obj = Register.objects.get(register_id=idd)
        # Optional photo update with strictly sanitized name
        # We don't overwrite the original registration obj.date or obj.time!
        obj.first_name = request.POST.get('first_name') or request.POST.get('fname') or obj.first_name
        obj.last_name = request.POST.get('last_name') or request.POST.get('lname') or obj.last_name
        obj.email = request.POST.get('email') or obj.email
        obj.date_of_birth = request.POST.get('date_of_birth') or request.POST.get('dob') or obj.date_of_birth
        obj.gender = request.POST.get('gender') or obj.gender
        obj.city = request.POST.get('city') or obj.city
        obj.country = request.POST.get('country') or obj.country
        # 🛡️ AUTHENTIC OTP LOCKDOWN: Prevent hijacked sessions from modifying the original registered mobile number.
        # obj.mobile = request.POST.get('mobile') or obj.mobile 
        obj.bio = request.POST.get('bio') or obj.bio
        obj.is_private = request.POST.get('is_private') == 'on'
        
        # Optional photo update with strictly sanitized name
        if 'photo' in request.FILES:
            my_file = request.FILES['photo']
            
            # --- MANDATORY BIOMETRIC LOCKDOWN ---
            # Any profile photo change MUST match the original registration photo.
            try:
                import numpy as np
                # Capture the new photo's face descriptor
                file_bytes = my_file.read()
                new_desc = get_face_descriptor(file_bytes)
                
                # Resolve the original registration photo (Source of Truth)
                reg_photo_path = os.path.join(settings.BASE_DIR, 'static', str(obj.reg_photo))
                reg_desc = get_face_descriptor(reg_photo_path)
                
                # --- SIBLING GUARD: BIOMETRIC DISAMBIGUATION ---
                # 1. Direct Check: If distance(new, original) > 0.60, it's a stranger.
                dist = np.linalg.norm(new_desc - reg_desc)
                
                # 2. Global Identity Audit: If this face matches a DIFFERENT user (e.g. brother) better, it's an intruder.
                known_faces = []
                static_dir = os.path.join(settings.BASE_DIR, 'static')
                for u in Register.objects.all():
                    anchor = u.reg_photo or u.photo
                    if anchor:
                        path_u = os.path.join(static_dir, str(anchor))
                        d_u = get_face_descriptor(path_u)
                        if d_u is not None:
                            known_faces.append((str(u.register_id), d_u))
                
                # Find the Best Match in the whole database (High Security 0.45 Threshold)
                best_match_id, best_match_dist = compare_faces(known_faces, new_desc, threshold=0.45)
                
                print(f"[AUDIT] Profile Edit Sibling-Guard: User={idd}, Match='{best_match_id}', Dist_to_Owner={dist:.4f}")
                
                if dist > 0.45: # Ultra-strict lockdown to separate look-alikes (Confirmed: Formal vs Headphones is 0.507)
                    context['msg'] = 'Access Denied: Biometric mismatch. The person in this photo is a close look-alike but does not match the registered owner (dist: {:.4f}).'.format(dist)
                    context['msg_type'] = 'error'
                    return render(request, "register/profile-edit.html", context)
                
                # If identified as someone else (sibling/intruder), reject even if they 'pass' the 0.60 owner check.
                if best_match_id != "Unknown" and best_match_id != str(idd):
                    context['msg'] = 'Sibling/Intruder Detected: This face is already registered to a different user. You cannot use it here.'
                    context['msg_type'] = 'error'
                    return render(request, "register/profile-edit.html", context)
                
                # Success: Reset pointer for saving
                my_file.seek(0)
            except Exception as e:
                print(f"Biometric check failed: {e}")
                context['msg'] = 'Security System Error: Disambiguation scan failed.'
                context['msg_type'] = 'error'
                return render(request, "register/profile-edit.html", context)
            
            fs = FileSystemStorage()
            # Create a clean filename to avoid space issues (Black image fix)
            ext = os.path.splitext(my_file.name)[1].lower()
            clean_name = f"profile_{idd}_{int(time.time())}{ext}"
            # Save directly to static root per user request
            saved_filename = fs.save(clean_name, my_file)
            obj.photo = saved_filename
            
        obj.save()
        
        # Sync with Login table
        Login.objects.filter(u_id=idd, type='user').update(username=obj.email)
        
        # Sync session variables to force UI updates immediately
        request.session['u_photo_fallback'] = str(obj.photo)
        request.session['u_first_name'] = obj.first_name
            
        context['j'] = obj
        context['msg'] = "Profile synchronized and updated successfully!"
        context['msg_type'] = "success"
    return render(request, "register/profile-edit.html", context)

def scorched_earth(request):
    from django.shortcuts import redirect
    ss = request.session.get('u_id')
    if ss:
        try:
            user = Register.objects.get(register_id=ss)
            
            # Manual Cascading to fix MySQL IntegrityError
            from register.models import Follower, FollowRequest, Message
            from image.models import LikePost, CommentPost, Image
            from generate.models import Permission
            from feedback.models import Feedback
            from complaint.models import Complaint
            
            Follower.objects.filter(follower_user_id=ss).delete()
            Follower.objects.filter(user_id=ss).delete()
            FollowRequest.objects.filter(requester_user_id=ss).delete()
            FollowRequest.objects.filter(target_user_id=ss).delete()
            Message.objects.filter(sender_id=ss).delete()
            Message.objects.filter(receiver_id=ss).delete()
            LikePost.objects.filter(user_id=ss).delete()
            CommentPost.objects.filter(user_id=ss).delete()
            Permission.objects.filter(user_id=ss).delete()
            Permission.objects.filter(upuser_id=ss).delete()
            Feedback.objects.filter(register_id=ss).delete()
            Complaint.objects.filter(register_id=ss).delete()
            
            # Wipe images and their dependencies manually before user delete
            user_img_qs = Image.objects.filter(register_id=ss)
            img_ids = list(user_img_qs.values_list('image_id', flat=True))
            if img_ids:
                Permission.objects.filter(image_id__in=img_ids).delete()
                LikePost.objects.filter(image_id__in=img_ids).delete()
                CommentPost.objects.filter(image_id__in=img_ids).delete()
                
            # Explicitly cascade image deletions to ensure DB constraints don't block Register delete
            # Delete physical files of the user's images
            static_dir = os.path.join(settings.BASE_DIR, 'static')
            for img in user_img_qs:
                for img_field in [img.photo, img.choose_file]:
                    if img_field:
                        fpath = os.path.join(static_dir, str(img_field))
                        if os.path.exists(fpath):
                            try:
                                os.remove(fpath)
                            except Exception:
                                pass
            user_img_qs.delete()
                
            # Signal `post_delete` will also fire, but the restrictive elements are now gone!
            # --- START OBLIVION PROTOCOL: BIOMETRIC SHREDDING ---
            static_dir = os.path.join(settings.BASE_DIR, 'static')
            for field in [user.reg_photo, user.photo]:
                if field:
                    # Resolve to actual file string, not ImageField object
                    field_str = str(field)
                    if field_str:
                        file_path = os.path.join(static_dir, field_str)
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                print(f"[OBLIVION PROTOCOL] Shredded biometric data: {file_path}")
                            except Exception as e:
                                print(f"[OBLIVION PROTOCOL] Error shredding {file_path}: {e}")
            # --- END OBLIVION PROTOCOL ---
            
            # Stop phantom logins by cascading Login credential deletion
            from login.models import Login
            Login.objects.filter(u_id=ss).delete()
            
            user.delete()
            if 'u_id' in request.session:
                del request.session['u_id']
        except Exception as e:
            print(f"Error deleting user (Scorched Earth): {e}")
            from django.http import HttpResponse
            return HttpResponse(f"CRITICAL ERROR ABORTING PURGE: {e}")
    return redirect('/login/login/')

def deactivate_account(request):
    from django.shortcuts import redirect
    ss = request.session.get('u_id')
    if ss:
        try:
            user = Register.objects.get(register_id=ss)
            user.status = 'hibernated'
            user.save()
            if 'u_id' in request.session:
                del request.session['u_id']
        except Register.DoesNotExist:
            pass
    return redirect('/login/login/')
