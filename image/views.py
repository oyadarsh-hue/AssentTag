# pyre-ignore-all-errors
from django.shortcuts import render # pyre-ignore
from django.contrib import messages as notices
from image.face_privacy import blur_private_face
from image.models import Image # pyre-ignore
import datetime # pyre-ignore
import dlib # pyre-ignore
import cv2 # pyre-ignore
import numpy as np # pyre-ignore
from django.core.files.storage import FileSystemStorage # pyre-ignore
from assentag import settings # pyre-ignore
from register.models import Register # pyre-ignore
import os # pyre-ignore
import requests # pyre-ignore
import json # pyre-ignore
import base64 # pyre-ignore
from django.core.files.base import ContentFile # pyre-ignore
from generate.models import Permission # pyre-ignore

from face_utils import get_face_descriptor, compare_faces, detector, predictor, face_rec_model, dlib_lock # pyre-ignore


from image.models import Image # pyre-ignore


def user_home_dashboard(request):
    # Fetch all photos backwards to show the newest at top
    uploaded_images = Image.objects.all().order_by('-image_id')

    context = {
        'images': uploaded_images  # Note: this matches {% for post in images %} in the HTML
    }

    return render(request, "index/index3", context)


def delete_post(request, id):
    """Deletes a post and redirects to dashboard."""
    from django.core.cache import cache # pyre-ignore
    try:
        img = Image.objects.get(image_id=id)
        # Check if uploader is the one deleting
        if str(img.register_id) == str(request.session.get('u_id')):
            img.delete()
            # Blast the dashboard memory caches so the ghost UI completely disintegrates
            cache.clear()
    except Image.DoesNotExist:
        pass
    return redirect(request.META.get('HTTP_REFERER', '/index/index3/'))

def add_text_post(request):
    from django.shortcuts import redirect # pyre-ignore
    ss = request.session.get('u_id')
    if not ss: return redirect('/login/login/')
    if request.method == 'POST':
        content = request.POST.get('text_content')
        if content:
            obj = Image()
            obj.date = datetime.datetime.today().date().strftime("%Y-%m-%d")
            obj.time = datetime.datetime.now().time().strftime("%H:%M")
            obj.register_id = ss
            obj.text_content = content
            obj.is_ghost_text = True
            obj.type = 'public'
            obj.visibility = 'public'
            obj.status = 'approved'
            obj.like = '0'
            obj.photo = '' 
            obj.choose_file = ''
            obj.save()
            notices.success(request, 'Your text post was published successfully.', extra_tags='post')
    return redirect('/index/index3/')

def add_story(request):
    ss = request.session.get('u_id')
    if not ss: return redirect('/login/login/')
    current_user = Register.objects.filter(register_id=ss).first()
    
    from register.models import Follower # pyre-ignore
    following = list(Follower.objects.filter(follower_user_id=ss).values_list('user_id', flat=True))
    followers = list(Follower.objects.filter(user_id=ss).values_list('follower_user_id', flat=True))
    mutual_ids = set(following).intersection(set(followers))
    mutual_friends = Register.objects.filter(register_id__in=mutual_ids)
    
    if request.method != 'POST':
        return render(request, "image/user_story_upload.html", {'current_user': current_user, 'friends': mutual_friends})
        
    my_file = request.FILES.get('story_media')
    live_photo_data = request.POST.get('live_photo')
    tagged_friends = request.POST.getlist('tagged_friends')
    if not tagged_friends:
        tagged_friends = []
    else:
        tagged_friends = [str(x).strip() for x in tagged_friends if str(x).strip()]
        
    if not my_file or not live_photo_data:
        return render(request, "image/user_story_upload.html", {'msg': 'Media and Live Verification are mandatory.', 'current_user': current_user, 'friends': mutual_friends, 'selected_friends': tagged_friends})

    try:
        # LIVE VERIFICATION
        format, imgstr = live_photo_data.split(';base64,') 
        img_bytes = base64.b64decode(imgstr)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        live_frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        live_rgb = cv2.cvtColor(live_frame, cv2.COLOR_BGR2RGB)
        
        upload_face_desc = None
        with dlib_lock:
            live_faces = detector(live_rgb)
        if len(live_faces) > 0:
            largest_face = max(live_faces, key=lambda rect: rect.width() * rect.height())
            with dlib_lock:
                shape = predictor(live_rgb, largest_face)
                upload_face_desc = np.array(face_rec_model.compute_face_descriptor(live_rgb, shape))
                
        # --- STRICT BIOMETRIC BASELINE (REGISTRATION ANCHOR) ---
        static_dir = os.path.join(settings.BASE_DIR, 'static')
        anchor_photo = getattr(current_user, 'reg_photo', None)
        
        if not current_user or not anchor_photo:
            return render(request, "image/user_story_upload.html", {'msg': 'Security Lockdown: No biometric registration (REG_PHOTO) found. Please contact Admin.', 'current_user': current_user, 'friends': mutual_friends, 'selected_friends': tagged_friends})

        uploader_profile_path = os.path.join(static_dir, str(anchor_photo))
        expected_face_desc = get_face_descriptor(uploader_profile_path)
        
        if expected_face_desc is None or upload_face_desc is None:
            return render(request, "image/user_story_upload.html", {'msg': 'Error: Biometric Audit Failed. Could not detect a clear face in your profile or live webcam capture.', 'current_user': current_user, 'friends': mutual_friends, 'selected_friends': tagged_friends})
            
        # --- SIBLING GUARD: BIOMETRIC DISAMBIGUATION ---
        all_users_faces = []
        for u in Register.objects.all():
            anchor_u = u.reg_photo or u.photo
            if anchor_u:
                desc_u = get_face_descriptor(os.path.join(static_dir, str(anchor_u)))
                if desc_u is not None:
                    all_users_faces.append((str(u.register_id), desc_u))
        
        # Identity Identification (Who is in front of the camera?)
        identified_id, identified_dist = compare_faces(all_users_faces, upload_face_desc, threshold=0.45)
        
        dist = np.linalg.norm(expected_face_desc - upload_face_desc) # pyre-ignore
        print(f"[AUDIT] Story Sibling-Guard: Session={ss}, Identified='{identified_id}', Dist_to_Owner={dist:.4f}")
        
        # If identified as someone else entirely, block access.
        if identified_id != "Unknown" and identified_id != str(ss):
            return render(request, "image/user_story_upload.html", {'msg': 'Sibling/Impersonator Warning: The system recognizes you as a different user. You cannot post content to this account.', 'current_user': current_user, 'friends': mutual_friends, 'selected_friends': tagged_friends})

        if dist > 0.45: # Ultra-strict lockdown to separate look-alikes (Confirmed: Formal vs Headphones is 0.507)
            return render(request, "image/user_story_upload.html", {'msg': 'Upload Rejected: The person in front of the camera is a look-alike but does not exactly match the registered owner (dist: {:.2f}).'.format(dist), 'current_user': current_user, 'friends': mutual_friends, 'selected_friends': tagged_friends})
            
        # Compile Known Faces (Uploader + Tagged Friends)
        known_faces = [(str(ss), expected_face_desc)]
        fobj = Register.objects.filter(register_id__in=tagged_friends)
        for f in fobj:
            anchor = getattr(f, 'reg_photo', None) or getattr(f, 'photo', None)
            if anchor:
                desc = get_face_descriptor(os.path.join(static_dir, str(anchor)))
                if desc is not None:
                    known_faces.append((str(f.register_id), desc))
                    
        # SAVE FILE
        from PIL import Image as PilImage # pyre-ignore
        import io, uuid # pyre-ignore
        im = PilImage.open(my_file)
        if im.mode in ("RGBA", "P"): im = im.convert("RGB")
        unique_name = f"forensic_story_{uuid.uuid4().hex[:8]}.jpg"
        img_io = io.BytesIO()
        im.save(img_io, format='JPEG', quality=95)
        img_io.seek(0)
        from django.core.files.uploadedfile import InMemoryUploadedFile # pyre-ignore
        fs = FileSystemStorage()
        jpg_file = InMemoryUploadedFile(img_io, None, unique_name, 'image/jpeg', img_io.getbuffer().nbytes, None)
        filename = fs.save(unique_name, jpg_file)
        
        # EXIF FACE DETECTION (Gaussian strategy)
        img_full_path = os.path.join(static_dir, filename)
        cv_img = cv2.imread(img_full_path)
        rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        with dlib_lock:
            faces = detector(rgb_img)
            
        # MULTI-STAGE SYNTHETIC DETECTOR (Phase 41)
        fpath = str(settings.BASE_DIR) + "/"+str(settings.STATIC_URL) + 'haarcascade_frontalface_default.xml'
        classifier = cv2.CascadeClassifier(fpath)
        gray_img_sc = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        upfaces = classifier.detectMultiScale(gray_img_sc, scaleFactor=1.2, minNeighbors=8, minSize=(60, 60))
            
        json_coords = []
        for face in faces:
            x, y = face.left(), face.top()
            w, h = face.right() - x, face.bottom() - y
            with dlib_lock:
                shape = predictor(rgb_img, face)
                face_desc = np.array(face_rec_model.compute_face_descriptor(rgb_img, shape))
                
            best_dist = float('inf')
            assigned_id = None
            
            for kname, kdesc in known_faces:
                # STRICT 0.50 match required (Phase 42). Tagged users not present will be dropped naturally.
                threshold = 0.50
                fd_dist = np.linalg.norm(kdesc - face_desc) # pyre-ignore
                if fd_dist < best_dist and fd_dist <= threshold:
                    best_dist = fd_dist
                    assigned_id = str(kname)
                
            json_coords.append({
                'user_id': assigned_id,
                'name': assigned_id if assigned_id else "Unknown",
                'x': x, 'y': y, 'w': w, 'h': h
            })
            
        # Inject HaarCascade detections that Dlib missed (Gemini/AI/Drawn Faces)
        for (hx, hy, hw, hh) in upfaces:
            hcx, hcy = hx + hw/2, hy + hh/2
            overlap = False
            for d in json_coords:
                dcx, dcy = d['x'] + d['w']/2, d['y'] + d['h']/2
                dist_centers = np.linalg.norm(np.array([hcx, hcy]) - np.array([dcx, dcy])) # pyre-ignore
                if dist_centers < max(hw, hh):
                    overlap = True
                    break
            
            if not overlap:
                print(f"[+] Story Multi-Stage Security: Caught a Phantom Face (x={hx}, y={hy}) missed by Biometrics!")
                json_coords.append({
                    'user_id': None,
                    'name': 'Unknown',
                    'x': int(hx), 'y': int(hy), 'w': int(hw), 'h': int(hh)
                })
                
        # --- UPLOADER PHYSICAL PRESENCE GUARD (Phase 42) ---
        uploader_present = any(str(c['user_id']) == str(ss) for c in json_coords)
        if not uploader_present:
            if os.path.exists(img_full_path):
                os.remove(img_full_path)
            return render(request, "image/user_story_upload.html", {'msg': 'Upload Rejected: Your registered profile face was not visually recognized in this story.', 'current_user': current_user, 'friends': mutual_friends, 'selected_friends': tagged_friends})
            
        import json, piexif, piexif.helper # pyre-ignore
        json_payload = json.dumps(json_coords)
        try:
            exif_dict = piexif.load(img_full_path)
        except Exception:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}
        if "Exif" not in exif_dict or exif_dict["Exif"] is None:
            exif_dict["Exif"] = {}
        exif_dict["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(json_payload)
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, img_full_path)
        
        # DB SAVE
        obj = Image()
        obj.date = datetime.datetime.today().date().strftime("%Y-%m-%d")
        obj.time = datetime.datetime.now().time().strftime("%H:%M")
        obj.register_id = ss
        obj.photo = filename
        obj.choose_file = filename
        obj.visibility = 'public'
        obj.type = 'public'
        obj.like = '0'
        obj.status = 'approved'
        obj.is_story = True
        obj.text_content = ''
        obj.save()
        
        # Dispatch Permissions
        ops = Permission()
        ops.image_id = obj.image_id
        ops.user_id = ss
        ops.status = 'approved'
        ops.upuser_id = ss
        ops.save()
        
        assigned_story_users = {str(c['user_id']) for c in json_coords if c.get('user_id')}
        
        for u_id in tagged_friends:
            if str(u_id) in assigned_story_users:
                tops = Permission()
                tops.image_id = obj.image_id
                tops.user_id = u_id
                tops.status = 'pending'
                tops.upuser_id = ss
                tops.save()
        
        notices.success(request, 'Your story was shared successfully.', extra_tags='upload')
        return redirect('/index/index3/')
    except Exception as e:
        return render(request, "image/user_story_upload.html", {'msg': f'Asset decryption failed: {e}', 'current_user': current_user, 'friends': mutual_friends, 'selected_friends': tagged_friends})

def view_story(request, story_id):
    ss = request.session.get('u_id')
    if not ss: return redirect('/login/login/')
    
    current_user = Register.objects.filter(register_id=ss).first()
    
    try:
        story = Image.objects.select_related('register').get(image_id=story_id, is_story=True)
    except Image.DoesNotExist:
        return redirect('/index/index3/')
        
    static_dir = os.path.join(settings.BASE_DIR, 'static')
    filepath = os.path.join(static_dir, str(story.photo))
    
    original_frame = cv2.imread(filepath)
    if original_frame is None:
        return redirect('/index/index3/')
        
    # --- DYNAMIC BLUR FOR STORIES ---
    try:
        import piexif, piexif.helper, json # pyre-ignore
        exif_dict = piexif.load(filepath)
        user_comment = exif_dict.get("Exif", {}).get(piexif.ExifIFD.UserComment)
        if user_comment:
            json_string = piexif.helper.UserComment.load(user_comment)
            if json_string:
                json_string = "".join(c for c in json_string if c.isprintable() and not c.isspace())
                json_coords = json.loads(json_string)
                img_h, img_w = original_frame.shape[:2]
                
                # Only Authorize the Uploader + Tagged Approvers
                authorized_ids = {str(story.register_id)}
                approved_perms = Permission.objects.filter(image_id=story.image_id, status='approved').values_list('user_id', flat=True)
                for ap in approved_perms:
                    authorized_ids.add(str(ap))
                    
                # The viewer is authorized IF they are the uploader, otherwise they only unblur IF their ID is in the approved map
                if str(ss) == str(story.register_id):
                    authorized_ids.add(str(ss))
                
                for face in json_coords:
                    is_authorized = False
                    if face.get('user_id') and str(face.get('user_id')) in authorized_ids:
                        is_authorized = True
                    elif face.get('name') and str(face.get('name')) in authorized_ids:
                        is_authorized = True
                        
                    if not is_authorized:
                        blur_private_face(original_frame, face)
    except Exception as e:
        return redirect('/index/index3/')

    # Final base64 stream directly to template
    _, buffer = cv2.imencode('.jpg', original_frame)
    img_b64 = base64.b64encode(buffer).decode('utf-8')
    
    # ---------------- SEQUENTIAL STORY ALGORITHM ----------------
    next_story_url = None
    prev_story_url = None
    try:
        from datetime import datetime, timedelta # pyre-ignore
        current_time = datetime.now()
        
        # Calculate Next Story (Forward chronological)
        potential_next = Image.objects.filter(
            register_id=story.register_id,
            is_story=True,
            image_id__gt=story.image_id
        ).order_by('image_id')
        
        for p in potential_next:
            try:
                p_dt = datetime.strptime(f"{p.date} {p.time}", "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    p_dt = datetime.strptime(f"{p.date} {p.time}", "%Y-%m-%d %H:%M")
                except ValueError:
                    continue
            if current_time - p_dt <= timedelta(hours=24):
                next_story_url = f"/image/view_story/{p.image_id}/"
                break
                
        # Calculate Previous Story (Backward chronological)
        potential_prev = Image.objects.filter(
            register_id=story.register_id,
            is_story=True,
            image_id__lt=story.image_id
        ).order_by('-image_id')
        
        for p in potential_prev:
            try:
                p_dt = datetime.strptime(f"{p.date} {p.time}", "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    p_dt = datetime.strptime(f"{p.date} {p.time}", "%Y-%m-%d %H:%M")
                except ValueError:
                    continue
            if current_time - p_dt <= timedelta(hours=24):
                prev_story_url = f"/image/view_story/{p.image_id}/"
                break
                
    except Exception as e:
        print(f"Story sequence failed: {e}")
    # -------------------------------------------------------------
    
    context = {
        'story': story,
        'image_b64': img_b64,
        'is_owner': str(story.register_id) == str(ss),
        'current_user': current_user,
        'next_story_url': next_story_url,
        'prev_story_url': prev_story_url
    }
    return render(request, "image/view_story.html", context)

def get_likers(request, post_id):
    from django.http import JsonResponse
    from image.models import LikePost
    if request.method == "GET":
        likes = LikePost.objects.filter(image_id=post_id).select_related('user')
        likers_data = []
        for like in likes:
            likers_data.append({
                'register_id': like.user.register_id,
                'first_name': like.user.first_name,
                'last_name': like.user.last_name or "",
                'email': like.user.email,
                'photo': str(like.user.photo) if like.user.photo else 'assets/user_icon.svg'
            })
        return JsonResponse({'status': 'success', 'likers': likers_data})
    return JsonResponse({'status': 'error', 'message': 'Invalid method'})

def add_image(request):
    ob=Image.objects.all()
    context={
        'a':ob
    }
    return render(request,"image/admin_photo_details.html",context)

from django_ratelimit.decorators import ratelimit # pyre-ignore

@ratelimit(key='ip', rate='5/m', block=True)
def add_image1(request):
    if request.method == 'POST':
        ss = request.session.get('u_id')  # CHANGED to u_id
        obj = Image()
        obj.date = datetime.datetime.today().date()
        obj.time = datetime.datetime.now().time()

        my_file = request.FILES['media']
        
        import filetype # pyre-ignore
        # Read the exact binary header to guarantee mathematical image validity, preventing fake extension exploits
        kind = filetype.guess(my_file.read(2048))
        my_file.seek(0) # Reset stream for Django

        if kind is None or not kind.mime.startswith('image/'):
            return render(request, "image/user-upload.html", {'msg': f'Security Alert: Unauthorized file payload detected! Expected image.', 'msg_type': 'error'})

        from register.models import Follower # pyre-ignore
        following = list(Follower.objects.filter(follower_user_id=ss).values_list('user_id', flat=True))
        followers = list(Follower.objects.filter(user_id=ss).values_list('follower_user_id', flat=True))
        mutual_ids = set(following).intersection(set(followers))
        mutual_friends = Register.objects.filter(register_id__in=mutual_ids)

        tagged_friends = request.POST.getlist('tagged_friends')
        if not tagged_friends:
            tagged_friends = []
        else:
            tagged_friends = [str(x).strip() for x in tagged_friends if str(x).strip()]

        live_photo_data = request.POST.get('live_photo')
        if not live_photo_data:
            user_profile = Register.objects.filter(register_id=ss).first()
            return render(request, "image/user-upload.html", {'msg': 'Live WebCam Photo is Required to Post! Please click Capture WebCam.', 'msg_type': 'error', 'selected_friends': tagged_friends, 'friends': mutual_friends, 'current_user': user_profile})

        upload_face_desc = None
        if live_photo_data:
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
                    desktop_save_path = os.path.join(desktop_dir, f"live_upload_face_{ss}_{int(time.time())}.jpg")
                    cv2.imwrite(desktop_save_path, live_frame)
                    print(f"[DEBUG] Saved live upload face to desktop: {desktop_save_path}")
                except Exception as e:
                    print(f"Failed to save live upload face to desktop: {e}")
                
                with dlib_lock:
                    live_faces = detector(live_rgb)
                if len(live_faces) > 0:
                    largest_face = max(live_faces, key=lambda rect: rect.width() * rect.height())
                    with dlib_lock:
                        shape = predictor(live_rgb, largest_face)
                        upload_face_desc = np.array(face_rec_model.compute_face_descriptor(live_rgb, shape))
            except Exception:
                pass

        # --- STRICT BIOMETRIC BASELINE (REGISTRATION ANCHOR) ---
        user_profile = Register.objects.filter(register_id=ss).first()
        static_dir = os.path.join(settings.BASE_DIR, 'static')
        anchor_photo = getattr(user_profile, 'reg_photo', None)
        
        if not user_profile or not anchor_photo:
            return render(request, "image/user-upload.html", {'msg': 'Security Lockdown: No biometric registration (REG_PHOTO) found. Please contact Admin to re-verify your identity.', 'msg_type': 'error', 'selected_friends': tagged_friends, 'friends': mutual_friends, 'current_user': user_profile})

        uploader_profile_path = os.path.join(static_dir, str(anchor_photo))
        expected_face_desc = get_face_descriptor(uploader_profile_path)
        
        if expected_face_desc is None or upload_face_desc is None:
            return render(request, "image/user-upload.html", {'msg': 'Error: Biometric Audit Failed. Could not detect a clear face in your profile or live webcam capture.', 'msg_type': 'error', 'selected_friends': tagged_friends, 'friends': mutual_friends, 'current_user': user_profile})
            
        # --- SIBLING GUARD: BIOMETRIC DISAMBIGUATION ---
        # Resolve all known faces for a full database identity audit
        all_users_faces = []
        for u in Register.objects.all():
            anchor = u.reg_photo or u.photo
            if anchor:
                desc = get_face_descriptor(os.path.join(static_dir, str(anchor)))
                if desc is not None:
                    all_users_faces.append((str(u.register_id), desc))
        
        # Identity Identification (Who is in front of the camera?)
        identified_id, identified_dist = compare_faces(all_users_faces, upload_face_desc, threshold=0.45)
        
        dist = np.linalg.norm(expected_face_desc - upload_face_desc) # pyre-ignore
        print(f"[AUDIT] Media Sibling-Guard: Session={ss}, Identified='{identified_id}', Dist_to_Owner={dist:.4f}")
        
        # If identified as someone else entirely, block access.
        if identified_id != "Unknown" and identified_id != str(ss):
            return render(request, "image/user-upload.html", {'msg': 'Sibling/Impersonator Warning: The system recognizes you as a different user. You cannot post content to this account.', 'msg_type': 'error', 'selected_friends': tagged_friends, 'friends': mutual_friends, 'current_user': user_profile})

        if dist > 0.45: # Ultra-strict lockdown to separate look-alikes (Confirmed: Formal vs Headphones is 0.507)
            return render(request, "image/user-upload.html", {'msg': 'Upload Rejected: The person in front of the camera is a look-alike but does not exactly match the registered owner (dist: {:.2f}).'.format(dist), 'msg_type': 'error', 'selected_friends': tagged_friends, 'friends': mutual_friends, 'current_user': user_profile})

        fs = FileSystemStorage()
        
        # -------- STRICT JPEG CONVERSION FOR EXIF COMPATIBILITY --------
        from PIL import Image as PilImage # pyre-ignore
        import io # pyre-ignore
        import uuid # pyre-ignore
        
        try:
            im = PilImage.open(my_file)
            if im.mode in ("RGBA", "P"):
                im = im.convert("RGB")
            elif im.mode != "RGB":
                im = im.convert("RGB")
                
            unique_name = str(uuid.uuid4())[:8] + "_" + os.path.splitext(my_file.name)[0] + ".jpg" # pyre-ignore
            img_io = io.BytesIO()
            im.save(img_io, format='JPEG', quality=95)
            img_io.seek(0)
            
            from django.core.files.uploadedfile import InMemoryUploadedFile # pyre-ignore
            jpg_file = InMemoryUploadedFile(img_io, None, unique_name, 'image/jpeg', img_io.getbuffer().nbytes, None)
            filename = fs.save(unique_name, jpg_file)
        except Exception as e:
            print(f"JPEG Conversion failed: {e}")
            filename = fs.save(my_file.name, my_file)

        obj.visibility = 'public'
        obj.type = 'public'
        obj.like = '0'
        obj.status = 'approved'
        obj.choose_file = str(filename)[:199] # pyre-ignore
        obj.photo = filename
        obj.register_id = ss
        
        # Validation passed for profile match
        obj.user_photo = user_profile.photo

        # STRICT DATABASE SCOPE LIMIT (Phase 41)
        fobj = Register.objects.filter(register_id__in=tagged_friends)
        
        # -------- LOAD REGISTERED FACES --------
        known_faces = [(str(ss), expected_face_desc)] # Always include the uploader implicitly

        # -------- LOAD REGISTERED FACES --------
        for f in fobj:

            name = str(f.register_id)  # Register primary key

            # ✅ use permanent registration anchor (fallback to photo)
            anchor_photo_f = getattr(f, 'reg_photo', None) or getattr(f, 'photo', None)
            if not anchor_photo_f:
                continue
                
            static_dir = os.path.join(settings.BASE_DIR, 'static')
            ffname = os.path.join(static_dir, str(anchor_photo_f))

            descriptor = get_face_descriptor(ffname)

            if descriptor is not None:
                known_faces.append((name, descriptor))
                print(f"[+] Loaded encoding for {name}")
            else:
                print(f"[!] No face found in {ffname}")

        print("finished")

        # -------- BLUR SECTION --------
        blur_strength = 99
        static_dir = os.path.join(settings.BASE_DIR, 'static')
        filepath = os.path.join(static_dir, str(filename))
        original_frame = cv2.imread(filepath)

        if original_frame is None:
            print("Image not loaded")
            return render(request, "image/user-upload.html", {'selected_friends': tagged_friends, 'friends': mutual_friends, 'current_user': user_profile})

        # Create two copies: base_frame for private viewing (unknowns blurred, friends clear)
        # public_frame for public feeds (unknowns blurred, friends blurred until approved)
        base_frame = original_frame.copy()
        public_frame = original_frame.copy()

        rgb_frame = cv2.cvtColor(original_frame, cv2.COLOR_BGR2RGB)
        with dlib_lock:
            faces = detector(rgb_frame)

        # -------- UPLOADER PRESENCE CHECK --------
        uploader_present = False
        face_data = [] # Store descriptor, name, coords to avoid recomputing

        for face in faces:
            with dlib_lock:
                shape = predictor(rgb_frame, face)
                descriptor = face_rec_model.compute_face_descriptor(rgb_frame, shape)
            descriptor = np.array(descriptor)

            # Extract original bounding box
            x = face.left()
            y = face.top()
            w = face.right() - face.left()
            h = face.bottom() - face.top()

            face_data.append({
                'descriptor': descriptor, 'name': 'Unknown', 'x': x, 'y': y, 'w': w, 'h': h
            })

        # --- MULTI-STAGE SYNTHETIC DETECTOR DISABLED ---
        # Removed HaarCascade injections as they cause false positive "Phantom Faces" on user chests/shirts.
        # Dlib's CNN/HOG detector is utilized exclusively for superior accuracy.

        # --- Assign each known user using a Greedy Distance Matrix ---
        matches = []
        for kname, kdesc in known_faces:
            # STRICT 0.50 threshold (Phase 42). Unmatched tagged users will naturally fall into the void.
            threshold = 0.50
            for idx, data in enumerate(face_data):
                dist = np.linalg.norm(kdesc - data['descriptor']) # pyre-ignore
                if dist <= threshold:
                    matches.append((dist, str(kname), idx))
        
        # Sort by shortest distance
        matches.sort(key=lambda x: x[0])
        
        assigned_faces = set()
        assigned_users = set()
        face_to_user = {} # face_idx -> (user_id, distance)
        
        for dist, kname, f_idx in matches:
            if kname not in assigned_users and f_idx not in assigned_faces:
                face_to_user[f_idx] = (kname, dist)
                assigned_faces.add(f_idx)
                assigned_users.add(kname)

        live_face_matches_upload = False

        # Find the single best match for the live webcam using infinite tolerance 
        # because they ALREADY passed strictly authenticated live verification
        best_live_dist = float('inf')
        best_live_idx = -1
        for idx, data in enumerate(face_data):
            dist_to_live = np.linalg.norm(upload_face_desc - data['descriptor']) # pyre-ignore
            if dist_to_live < best_live_dist: 
                best_live_dist = dist_to_live
                best_live_idx = idx

        for idx, data in enumerate(face_data):
            if idx in face_to_user:
                data['name'] = face_to_user[idx][0]
            else:
                data['name'] = "Unknown"

        # Ensure the Uploader was actually assigned to a face naturally via greedy matcher
        uploader_present = any(str(data['name']) == str(ss) for data in face_data)
        
        if not uploader_present:
            if os.path.exists(filepath):
                os.remove(filepath)
            return render(request, "image/user-upload.html", {
                'msg': 'Upload Rejected: Your registered profile face was not visually recognized in this photo.',
                'msg_type': 'error',
                'selected_friends': tagged_friends,
                'friends': mutual_friends,
                'current_user': user_profile
            })

        # Save Image to generate its Primary Key before we assign it to Permissions
        obj.save()
        
        # -------- ADVANCED EXIF METADATA STEGANOGRAPHY PIPELINE --------
        # To achieve High-Speed Zero-Storage without the Database, we embed the Face Coordinates
        # directly inside the physical image binary as an invisible Exif tag.
        import json, piexif, piexif.helper # pyre-ignore
        json_coords = []
        for data in face_data:
            assigned_user_pk = None
            if data['name'] != "Unknown":
                assigned_user_pk = data['name']
            
            json_coords.append({
                'user_id': assigned_user_pk,
                'x': data['x'],
                'y': data['y'],
                'w': data['w'],
                'h': data['h']
            })
            
        json_payload = json.dumps(json_coords)
        
        try:
            exif_dict = piexif.load(filepath)
        except Exception:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}
            
        try:
            if "Exif" not in exif_dict or exif_dict["Exif"] is None: # pyre-ignore
                exif_dict["Exif"] = {} # pyre-ignore
                
            # Inject JSON as ascii bytes directly into the Image's Exif UserComment field
            exif_dict["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(json_payload) # pyre-ignore
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, filepath)
            print("Successfully embedded JSON into Image EXIF.")
        except Exception as e:
            print(f"EXIF Encoding Failed: {e}")

        # -------- SAVE UPLOADER APPROVED PERMISSION --------
        if ss is not None:
            ops = Permission()
            ops.image_id = obj.image_id
            ops.user_id = ss
            ops.status = 'approved'
            ops.upuser_id = ss
            ops.save()

        # -------- GENERATE PERMISSIONS FOR RECOGNIZED FACES & TAGGED FRIENDS --------
        notified_users = set()

        # Users requested NOT to send notifications to passively recognized faces.
        # Only explicitly tagged friends should receive a notification.
        # for data in face_data:
        #     name = data['name']
        #     if name != "Unknown" and name is not None:
        #         notified_users.add(str(name))
                
        for friend_id in tagged_friends:
            # Only send notification if the Tagged Friend was ACTUALLY found physically in the image!
            if str(friend_id) in assigned_users:
                notified_users.add(str(friend_id))

        for u_id in notified_users:
            # Skip uploader, they are already approved
            if str(ss) == str(u_id):
                continue

            # Create the Pending Permission for this target user.
            ops = Permission()
            ops.image_id = obj.image_id
            ops.user_id = u_id
            ops.status = 'pending'
            ops.upuser_id = ss
            ops.save()

        from register.models import Follower # pyre-ignore
        ss_val = request.session.get('u_id')
        c = {'msg': 'Photo uploaded and processed successfully', 'msg_type': 'success', 'redirect_url': '/index/index3', 'current_user': user_profile}
        if ss_val:
            following_p = list(Follower.objects.filter(follower_user_id=ss_val).values_list('user_id', flat=True))
            followers_p = list(Follower.objects.filter(user_id=ss_val).values_list('follower_user_id', flat=True))
            mutual_ids_p = set(following_p).intersection(set(followers_p))
            c['friends'] = Register.objects.filter(register_id__in=mutual_ids_p)
        return render(request, "image/user-upload.html", c)

    ss = request.session.get('u_id')
    current_user = Register.objects.filter(register_id=ss).first() if ss else None
    if ss:
        from register.models import Follower # pyre-ignore
        following = list(Follower.objects.filter(follower_user_id=ss).values_list('user_id', flat=True))
        followers = list(Follower.objects.filter(user_id=ss).values_list('follower_user_id', flat=True))
        mutual_ids = set(following).intersection(set(followers))
        mutual_friends = Register.objects.filter(register_id__in=mutual_ids)
        return render(request, "image/user-upload.html", {'friends': mutual_friends, 'current_user': current_user})

    return render(request, "image/user-upload.html", {'current_user': current_user})


from django.shortcuts import redirect # pyre-ignore


from django.http import JsonResponse # pyre-ignore
import base64 # pyre-ignore

def review_tag(request, perm_id):
    ss = request.session.get('u_id')
    if not ss: return redirect('/login/login/')
    return render(request, "temp/verify_tag.html", {'perm_id': perm_id})

def verify_live_face(request, perm_id):
    ss = request.session.get('u_id')
    if not ss: return JsonResponse({'status': 'error', 'message': 'Not logged in'})
    
    if request.method == 'POST':
        live_photo_data = request.POST.get('live_photo')
        if not live_photo_data:
            return JsonResponse({'status': 'error', 'message': 'No live photo provided'})
        
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
                desktop_save_path = os.path.join(desktop_dir, f"live_verified_face_{perm_id}_{int(time.time())}.jpg")
                cv2.imwrite(desktop_save_path, live_frame)
                print(f"[DEBUG] Saved live verified face to desktop: {desktop_save_path}")
            except Exception as e:
                print(f"Failed to save live verified face to desktop: {e}")
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'Invalid image format'})

        with dlib_lock:
            live_faces = detector(live_rgb)
        if len(live_faces) == 0:
            return JsonResponse({'status': 'error', 'message': 'No face detected in webcam'})
        
        largest_face = max(live_faces, key=lambda rect: rect.width() * rect.height())
        with dlib_lock:
            shape = predictor(live_rgb, largest_face)
            live_desc = np.array(face_rec_model.compute_face_descriptor(live_rgb, shape))

        u_reg = Register.objects.filter(register_id=ss).first()
        if not u_reg or not u_reg.photo:
            return JsonResponse({'status': 'error', 'message': 'No profile photo found to match against.'})
            
        static_dir = os.path.join(settings.BASE_DIR, 'static')
        upath = os.path.join(static_dir, str(u_reg.photo))
        if not os.path.exists(upath):
            return JsonResponse({'status': 'error', 'message': 'Profile photo file missing.'})
            
        u_desc = get_face_descriptor(upath)
        if u_desc is None:
            return JsonResponse({'status': 'error', 'message': 'Could not process your profile photo.'})

        dist = np.linalg.norm(live_desc - u_desc) # pyre-ignore
        if dist > 0.45: # Standard Authentication threshold
            return JsonResponse({'status': 'error', 'message': f'SECURITY ALERT: Live Face does not match the registered profile owner! Dist: {dist:.2f}'})
            
        request.session[f'verified_tag_{perm_id}'] = True
        return JsonResponse({'status': 'success'})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def approve_tag(request, perm_id):
    import os, json, piexif, piexif.helper, cv2, dlib, numpy as np # pyre-ignore
    from django.conf import settings # pyre-ignore
    from django.core.cache import cache # pyre-ignore
    from face_utils import get_face_descriptor, face_rec_model, predictor # pyre-ignore
    from image.models import Image # pyre-ignore
    from register.models import Register # pyre-ignore

    ss = request.session.get('u_id')
    if not ss: return redirect('/login/login/')
    
    if not request.session.get(f'verified_tag_{perm_id}'):
        return redirect(f'/image/review-tag/{perm_id}/')
        
    perm = Permission.objects.filter(per_id=perm_id, user_id=ss).first()
    if perm:
        perm.status = 'approved'
        perm.save()
        request.session.pop(f'verified_tag_{perm_id}', None)
        notices.success(request, 'Your consent was saved. Your tagged photo is now approved.', extra_tags='verification')
        
        # --- PERMANENT EXIF OVERRIDE ---
        img_obj = Image.objects.filter(image_id=perm.image_id).first()
        viewer_obj = Register.objects.filter(register_id=int(ss)).first()
        
        if img_obj and img_obj.photo and viewer_obj and viewer_obj.photo:
            static_dir = os.path.join(settings.BASE_DIR, 'static')
            viewer_photo_path = os.path.join(static_dir, str(viewer_obj.photo))
            filepath = os.path.join(static_dir, str(img_obj.photo))
            
            if os.path.exists(viewer_photo_path) and os.path.exists(filepath):
                viewer_desc = get_face_descriptor(viewer_photo_path)
                
                try:
                    exif_dict = piexif.load(filepath)
                    user_comment = exif_dict.get("Exif", {}).get(piexif.ExifIFD.UserComment)
                    
                    if user_comment and viewer_desc is not None:
                        json_string = piexif.helper.UserComment.load(user_comment)
                        if json_string:
                            json_string = "".join(c for c in json_string if c.isprintable() and not c.isspace())
                            json_coords = json.loads(json_string)
                            
                            frame = cv2.imread(filepath)
                            if frame is not None:
                                h, w = frame.shape[:2]
                                scale_fac = 1.0
                                if max(h, w) > 400:
                                    scale_fac = 400.0 / max(h, w)
                                    frame = cv2.resize(frame, (int(w * scale_fac), int(h * scale_fac)))
                                    
                                updated = False
                                already_assigned = any(str(fd.get('user_id')) == str(ss) for fd in json_coords)
                                
                                if not already_assigned:
                                    best_dist = float('inf')
                                    best_face_data = None
                                    
                                    for face_data in json_coords:
                                        if not face_data.get('user_id'): # Null face
                                            x = int(face_data['x'] * scale_fac)
                                            y = int(face_data['y'] * scale_fac)
                                            w_face = int(face_data['w'] * scale_fac)
                                            h_face = int(face_data['h'] * scale_fac)
                                            
                                            h_img, w_img = frame.shape[:2] # pyre-ignore
                                            y1, y2 = max(0, y), min(h_img, y + h_face)
                                            x1, x2 = max(0, x), min(w_img, x + w_face)
                                            
                                            if w_face > 0 and h_face > 0:
                                                try:
                                                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # pyre-ignore
                                                    rect = dlib.rectangle(x1, y1, x2, y2) # pyre-ignore
                                                    shape = predictor(rgb_frame, rect) # pyre-ignore
                                                    face_desc = np.array(face_rec_model.compute_face_descriptor(rgb_frame, shape)) # pyre-ignore
                                                    dist = np.linalg.norm(viewer_desc - face_desc) # pyre-ignore
                                                    
                                                    # Use generous threshold here (infinity essentially) because the user ALREADY passed the strict Live Webcam 
                                                    # Verification step! This is just to identify WHICH null box belongs to them in the image EXIF.
                                                    if dist < best_dist:
                                                        best_dist = dist
                                                        best_face_data = face_data
                                                except Exception:
                                                    pass
                                                    
                                    if best_face_data is not None:
                                        best_face_data['user_id'] = str(ss) # pyre-ignore
                                        updated = True
                                                    
                                    if updated:
                                        new_json_string = json.dumps(json_coords)
                                        if exif_dict and "Exif" in exif_dict: # pyre-ignore
                                            exif_dict["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(new_json_string) # pyre-ignore
                                            exif_bytes = piexif.dump(exif_dict)
                                            piexif.insert(exif_bytes, filepath)
                                        
                                        # Clear specific caches for this image so it reloads immediately

                                    cache.delete_pattern(f"feed_{img_obj.image_id}_*") 
                                    cache.clear() # Blast cache to refresh Dashboard
                except Exception as e:
                    print(f"EXIF update failed on approval: {e}")
                    
    return redirect('/index/index4/')

def reject_tag(request, perm_id):
    ss = request.session.get('u_id')
    if not ss: return redirect('/login/login/')
    
    if not request.session.get(f'verified_tag_{perm_id}'):
        return redirect(f'/image/review-tag/{perm_id}/')
        
    perm = Permission.objects.filter(per_id=perm_id, user_id=ss).first()
    if perm:
        perm.status = 'rejected'
        perm.save()
        request.session.pop(f'verified_tag_{perm_id}', None)
        

            
    return redirect('/index/index4/')

from image.models import LikePost, CommentPost # pyre-ignore

def like_post(request, image_id):
    ss = request.session.get('u_id')
    if not ss: return redirect('/login/login/')
    
    img = Image.objects.filter(image_id=image_id).first()
    if img:
        existing_like = LikePost.objects.filter(image=img, user_id=ss).first()
        if existing_like:
            existing_like.delete() # Toggle unlike
        else:
            LikePost.objects.create(image=img, user_id=ss)
            
    return redirect('/index/index3/')

def add_comment(request, image_id):
    ss = request.session.get('u_id')
    if not ss: return redirect('/login/login/')
    
    if request.method == 'POST':
        content = request.POST.get('comment', '').strip()[:500]
        if content:
            img = Image.objects.filter(image_id=image_id).first()
            if img:
                CommentPost.objects.create(image=img, user_id=ss, text=content)
                notices.success(request, 'Your comment was added successfully.', extra_tags='post')
    
    return redirect(f'/index/index3/#comments-{image_id}')

def delete_comment(request, comment_id):
    ss = request.session.get('u_id')
    if not ss: return redirect('/login/login/')
    
    comment = CommentPost.objects.filter(comment_id=comment_id).select_related('image').first()
    if comment:
        # Both Comment Author OR Post Author have the architectural clearance to delete it
        if int(comment.user_id) == int(ss) or int(comment.image.register_id) == int(ss):
            comment.delete()
            
    return redirect(request.META.get('HTTP_REFERER', '/index/index3/'))



def serve_dynamic_image(request, image_id):
    from django.conf import settings # pyre-ignore
    from django.http import HttpResponse, Http404 # pyre-ignore
    from .models import Image # pyre-ignore
    import os # pyre-ignore

    try:
        img_obj = Image.objects.filter(image_id=image_id).first()
        if not img_obj or not img_obj.photo: 
            raise Http404("Image not found")

        static_dir = os.path.join(settings.BASE_DIR, 'static')
        filepath = os.path.join(static_dir, str(img_obj.photo))
        if not os.path.exists(filepath):
            raise Http404("Physical image file not found")
            
        import cv2, numpy as np, piexif, piexif.helper, json # pyre-ignore
        
        # Load the raw image into OpenCV memory
        im = cv2.imread(filepath)
        if im is None:
            raise Http404("Failed to decode image")
            
        img_h, img_w = im.shape[:2]
        
        # Determine who the viewer is
        ss = request.session.get('u_id')
        authorized_ids = {str(img_obj.register_id)} # Uploader is always authorized
        
        # Fetch approved tags
        from generate.models import Permission # pyre-ignore
        for perm in Permission.objects.filter(image_id=image_id, status='approved'):
            authorized_ids.add(str(perm.user_id))
            
        # Parse EXIF to find coordinate geometry map
        try:
            exif_dict = piexif.load(filepath)
            user_comment = exif_dict.get("Exif", {}).get(piexif.ExifIFD.UserComment)
            if user_comment:
                json_string = piexif.helper.UserComment.load(user_comment)
                if json_string:
                    json_string = "".join(c for c in json_string if c.isprintable() and not c.isspace())
                    json_coords = json.loads(json_string)
                    
                    # Intercept and physically scramble unauthorized faces
                    for face in json_coords:
                        is_authorized = False
                        if face.get('user_id') and str(face.get('user_id')) in authorized_ids:
                            is_authorized = True
                        elif face.get('name') and str(face.get('name')) in authorized_ids:
                            is_authorized = True
                            
                        # Uploader Name Match Safe-Guard
                        if not is_authorized and face.get('name') and str(face.get('name')) == str(img_obj.register_id):
                            is_authorized = True
                            
                        if not is_authorized:
                            blur_private_face(im, face)

            # -------- HIGH SECURITY: ANTI-SCREENSHOT STEGANOGRAPHIC TRACING --------
            # Embed the mathematical footprint of the current VIEWER into the image pixels.
            # This survives basic screenshots/cropping, enabling Traitor Tracing.
            if ss:
                overlay = im.copy()
                h, w = im.shape[:2]
                watermark_text = f"AUTH VIEWER: {ss} | ASSENT_TAG_SECURE"
                # Diagonal/Center placement
                cv2.putText(overlay, watermark_text, (int(w*0.05), int(h*0.95)), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(overlay, watermark_text, (int(w*0.05), int(h*0.05)), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                # Alpha blend at 3% opacity - invisible to the naked eye but mathematically recoverable via histogram equalization
                cv2.addWeighted(overlay, 0.03, im, 0.97, 0, im)

        except Exception as e:
            raise Http404("Privacy processing unavailable") from e
            
        # Compress back to JPEG and construct the network payload
        ret, buffer = cv2.imencode('.jpg', im, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ret:
            raise Http404("Failed to encode image")
            
        image_data = buffer.tobytes()
            
        res = HttpResponse(image_data, content_type='image/jpeg')
        res['Cache-Control'] = 'no-cache, max-age=0' # Prevent caching so different users see different blurry states
        return res
    except Exception as e:
        print(f"serve_dynamic_image error: {e}")
        return HttpResponse(status=404)

def serve_dynamic_notif(request, image_id, target_id):
    from django.conf import settings # pyre-ignore
    from django.http import HttpResponse, Http404 # pyre-ignore
    from .models import Image # pyre-ignore
    import os # pyre-ignore

    try:
        img_obj = Image.objects.filter(image_id=image_id).first()
        if not img_obj or not img_obj.photo: 
            raise Http404("Image not found")

        static_dir = os.path.join(settings.BASE_DIR, 'static')
        filepath = os.path.join(static_dir, str(img_obj.photo))
        if not os.path.exists(filepath):
            raise Http404("Physical image file not found")
            
        import piexif, piexif.helper, json # pyre-ignore
        from face_utils import get_face_descriptor, predictor, face_rec_model # pyre-ignore
        import cv2, dlib, numpy as np # pyre-ignore
        
        target_obj = Register.objects.filter(register_id=int(target_id)).first()
        target_desc = None
        if target_obj and target_obj.photo:
            target_photo_path = os.path.join(static_dir, str(target_obj.photo))
            if os.path.exists(target_photo_path):
                target_desc = get_face_descriptor(target_photo_path)
                
        # Physical Server-Side Blurring for Notifications!
        import cv2, numpy as np, piexif, piexif.helper, json # pyre-ignore
        
        im = cv2.imread(filepath)
        if im is None:
            raise Http404("Failed to load image")
            
        img_h, img_w = im.shape[:2]
        
        # In notifications, ONLY the uploader and the tag target (the viewer) are authorized
        authorized_ids = {str(img_obj.register_id), str(target_id)}
        
        try:
            exif_dict = piexif.load(filepath)
            user_comment = exif_dict.get("Exif", {}).get(piexif.ExifIFD.UserComment)
            if user_comment:
                json_string = piexif.helper.UserComment.load(user_comment)
                if json_string:
                    json_string = "".join(c for c in json_string if c.isprintable() and not c.isspace())
                    json_coords = json.loads(json_string)
                    
                    for face in json_coords:
                        is_authorized = False
                        if face.get('user_id') and str(face.get('user_id')) in authorized_ids:
                            is_authorized = True
                        elif face.get('name') and str(face.get('name')) in authorized_ids:
                            is_authorized = True
                            
                        # Uploader Name Match Safe-Guard
                        if not is_authorized and face.get('name') and str(face.get('name')) == str(img_obj.register_id):
                            is_authorized = True
                            
                        # If the face is NOT the uploader and NOT the viewer evaluating the tag, DESTROY IT geometrically
                        if not is_authorized:
                            blur_private_face(im, face)

        except Exception as e:
            raise Http404("Privacy processing unavailable") from e
            
        ret, buffer = cv2.imencode('.jpg', im, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ret:
            raise Http404("Failed to encode image")
            
        image_data = buffer.tobytes()
            
        res = HttpResponse(image_data, content_type='image/jpeg')
        res['Cache-Control'] = 'no-cache, max-age=0' # MUST NOT CACHE!
        return res
    except Exception as e:
        print(f"serve_dynamic_notif error: {e}")
        return HttpResponse(status=404)

def serve_profile_image(request, user_id):
    import cv2, os, numpy as np # pyre-ignore
    from django.conf import settings # pyre-ignore
    from django.http import HttpResponse, Http404 # pyre-ignore
    from register.models import Register # pyre-ignore
    from django.core.cache import cache # pyre-ignore

    # Distinct cache key for tiny profiles
    cache_key = f"profile_img_fast_{user_id}"
    cached_bytes = cache.get(cache_key)
    if cached_bytes:
        res = HttpResponse(cached_bytes, content_type='image/jpeg')
        res['Cache-Control'] = 'public, max-age=604800'
        return res

    user_obj = Register.objects.filter(register_id=user_id).first()
    if not user_obj or not user_obj.photo: 
        return HttpResponse(status=404)

    filepath = os.path.join(settings.MEDIA_ROOT, user_obj.photo)
    if not os.path.exists(filepath):
        return HttpResponse(status=404)

    try:
        frame = cv2.imread(filepath)
        if frame is None:
            return HttpResponse(status=404)

        # Ultra-fast resize for avatars (max 100px)
        h, w = frame.shape[:2]
        if max(h, w) > 100:
            scale_fac = 100.0 / max(h, w)
            frame = cv2.resize(frame, (int(w * scale_fac), int(h * scale_fac)), interpolation=cv2.INTER_AREA)

        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ret:
            return HttpResponse(status=500)

        buffer_bytes = buffer.tobytes()
        cache.set(cache_key, buffer_bytes, timeout=60*60*24*7) # Cache for 7 days
        
        response = HttpResponse(buffer_bytes, content_type='image/jpeg')
        response['Cache-Control'] = 'public, max-age=604800'
        return response
    except Exception as e:
        print(f"serve_profile_image error: {e}")
        return HttpResponse(status=500)
