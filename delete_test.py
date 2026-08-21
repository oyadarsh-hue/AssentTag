import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')
django.setup()

from register.models import Register
from django.db import transaction, IntegrityError

user = Register.objects.last()
if user:
    ss = user.register_id
    try:
        with transaction.atomic():
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

            user.delete()
            print("DELETION SUCCESSFUL!")
            # Rollback to not actually delete them
            raise Exception("Rollback")
    except IntegrityError as e:
        print(f"INTEGRITY ERROR: {e}")
    except Exception as e:
        if str(e) == "Rollback":
            print("Finished successfully")
        else:
            print(f"Other error: {e}")
