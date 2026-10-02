from django.db import models


# Create your models here.


class Login(models.Model):
    login_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=45)
    password = models.CharField(max_length=45)
    type = models.CharField(max_length=45)
    u_id = models.IntegerField()
    class Meta:
        #managed = False
        db_table = 'login'


class ConversationTimer(models.Model):
    """One shared timer per unordered pair; changes affect future messages."""
    user_low = models.ForeignKey('register.Register', on_delete=models.CASCADE, related_name='+')
    user_high = models.ForeignKey('register.Register', on_delete=models.CASCADE, related_name='+')
    duration = models.PositiveIntegerField(default=0)
    revision = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey('register.Register', on_delete=models.SET_NULL, null=True, related_name='+')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user_low', 'user_high'], name='unique_chat_timer'),
            models.CheckConstraint(check=models.Q(user_low__lt=models.F('user_high')), name='ordered_chat_pair'),
            models.CheckConstraint(check=models.Q(duration__in=[0, 60, 86400, 604800, 7776000]), name='valid_chat_duration'),
        ]

