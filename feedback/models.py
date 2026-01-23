from django.db import models

# Create your models here.

class Feedback(models.Model):
    f_id = models.AutoField(primary_key=True)
    feedback = models.CharField(max_length=45)
    date = models.DateField()
    time = models.DateTimeField()
    u_id = models.IntegerField()
    topic = models.CharField(max_length=45)
    rating = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'feedback'
