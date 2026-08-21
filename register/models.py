from django.db import models

# Create your models here.



class Register(models.Model):
    register_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=45)
    last_name = models.CharField(max_length=45)
    email = models.CharField(max_length=45)
    date_of_birth = models.CharField(max_length=45)
    gender = models.CharField(max_length=45)
    city = models.CharField(max_length=50)
    mobile = models.CharField(max_length=50)
    bio = models.CharField(max_length=500)
    password = models.CharField(max_length=50)
    confirm = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    photo = models.CharField(max_length=500)
    reg_photo = models.CharField(max_length=500)
    date = models.DateField()
    time = models.DateTimeField()
    status = models.CharField(max_length=15, default='pending')
    is_private = models.BooleanField(default=False)

    class Meta:
        #managed = False
        db_table = 'register'


class Follower(models.Model):
    follower_id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    follower_user = models.ForeignKey('Register', models.DO_NOTHING, related_name='following_set')
    user = models.ForeignKey('Register', models.DO_NOTHING, related_name='followers_set')

    class Meta:
        managed = False
        db_table = 'follower'
        unique_together = (('user', 'follower_user'),)

class FollowRequest(models.Model):
    request_id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    requester_user = models.ForeignKey('Register', models.CASCADE, related_name='follow_requests_sent')
    target_user = models.ForeignKey('Register', models.CASCADE, related_name='follow_requests_received')

    class Meta:
        managed = False
        db_table = 'follow_request'
        unique_together = (('requester_user', 'target_user'),)

class Message(models.Model):
    message_id = models.AutoField(primary_key=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.IntegerField(default=0)
    receiver = models.ForeignKey('Register', models.DO_NOTHING, related_name='received_messages')
    sender = models.ForeignKey('Register', models.DO_NOTHING, related_name='sent_messages')
    is_disappearing = models.BooleanField(default=False)

    class Meta:
        # managed = False
        db_table = 'message'

from django.db.models.signals import post_delete
from django.dispatch import receiver
import os
from django.conf import settings

@receiver(post_delete, sender=Register)
def auto_delete_user_media(sender, instance, **kwargs):
    """
    Asynchronous Deletion Protocol: Automatically wipes orphaned Image arrays 
    and physical files whenever a master User account is purged.
    """
    # Import inside to avoid circular dependency
    from image.models import Image
    from login.models import Login
    from generate.models import Permission
    
    # Wipe login credentials
    Login.objects.filter(u_id=instance.register_id, type='user').delete()
    
    # Wipe associated images and their physical files
    user_images = Image.objects.filter(register_id=instance.register_id)
    for img in user_images:
        if img.photo:
            path = os.path.join(settings.MEDIA_ROOT, img.photo)
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
        img.delete()
        
    # Wipe permissions/tags related to this user
    Permission.objects.filter(user_id=instance.register_id).delete()
    
    # Wipe profile photos
    for photo_attr in ['photo', 'reg_photo']:
        photo = getattr(instance, photo_attr, None)
        if photo:
            path = os.path.join(settings.MEDIA_ROOT, photo)
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
