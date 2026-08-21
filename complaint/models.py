from django.db import models
from register.models import Register
# Create your models here.

class Complaint(models.Model):
    complaint_id = models.AutoField(primary_key=True)
    date = models.DateField()
    time = models.TimeField()
    complaint = models.CharField(max_length=200)
    # register_id = models.IntegerField()
    register=models.ForeignKey(Register,on_delete=models.CASCADE)
    subject = models.CharField(max_length=45)
    urgency = models.CharField(max_length=45)
    reply = models.CharField(max_length=45)
    class Meta:
        # managed = False
        db_table = 'complaint'
