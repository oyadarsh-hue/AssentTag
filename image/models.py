from django.db import models
from register.models import Register
# Create your models here.



class Image(models.Model):
    image_id =  models.AutoField(primary_key=True)
    #register_id = models.IntegerField()

    date = models.CharField(max_length=45)
    time = models.CharField(max_length=45)
    photo = models.CharField(max_length=200, blank=True, null=True) # made optional for text posts
    visibility = models.CharField(max_length=45, blank=True, null=True)
    choose_file = models.CharField(max_length=200, blank=True, null=True)
    type = models.CharField(max_length=45)
    like = models.CharField(max_length=45)
    status = models.CharField(max_length=45)
    register = models.ForeignKey(Register, on_delete=models.CASCADE)
    
    # New Fields for Ghost Text (Anti-Shoulder Surfing)
    text_content = models.TextField(blank=True, null=True)
    is_ghost_text = models.BooleanField(default=False)
    
    # New Field for Neon Silhouette Stories
    is_story = models.BooleanField(default=False)
    
    class Meta:
        #managed = False
        db_table = 'image'

from django.db.models.signals import post_delete
from django.dispatch import receiver
import os
from django.conf import settings

@receiver(post_delete, sender=Image)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes the file from filesystem when corresponding `Image` object is deleted.
    """
    if instance.photo:
        filepath = os.path.join(settings.MEDIA_ROOT, instance.photo)
        if os.path.isfile(filepath):
            os.remove(filepath)
            
    # Also delete the choose_file if it points to a different physical asset
    if instance.choose_file and instance.choose_file != instance.photo:
        filepath = os.path.join(settings.MEDIA_ROOT, instance.choose_file)
        if os.path.isfile(filepath):
            os.remove(filepath)

class LikePost(models.Model):
    like_id = models.AutoField(primary_key=True)
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(Register, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'like_post'
        unique_together = ('image', 'user') # One like per user per post

class CommentPost(models.Model):
    comment_id = models.AutoField(primary_key=True)
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(Register, on_delete=models.CASCADE)
    text = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'comment_post'
