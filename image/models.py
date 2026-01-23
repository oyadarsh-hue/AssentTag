from django.db import models

# Create your models here.



class Image(models.Model):
    image_id =  models.AutoField(primary_key=True)
    register_id = models.IntegerField()
    date = models.CharField(max_length=45)
    time = models.CharField(max_length=45)
    photo = models.CharField(max_length=200)
    visibility = models.CharField(max_length=45)
    class Meta:
        managed = False
        db_table = 'image'
