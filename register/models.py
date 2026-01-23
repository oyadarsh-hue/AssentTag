from django.db import models

# Create your models here.



class Register(models.Model):
    register_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=45)
    last_name = models.CharField(max_length=45)
    email = models.CharField(max_length=45)
    date_of_birth = models.CharField(max_length=45)
    gender = models.CharField(max_length=45)
    city = models.CharField(max_length=45)
    mobile = models.CharField(max_length=45)
    bio = models.CharField(max_length=45)
    password = models.CharField(max_length=45)
    confirm = models.CharField(max_length=45)
    country = models.CharField(max_length=45)
    photo = models.CharField(max_length=200)
    date = models.DateField()
    time = models.DateTimeField()
    status = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'register'



