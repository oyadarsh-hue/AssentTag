from django.db import models
from image.models import Image

class Permission(models.Model):
    per_id = models.AutoField(primary_key=True)

    image = models.ForeignKey(
        Image,
        on_delete=models.CASCADE,

    )

    user_id = models.IntegerField()
    status = models.CharField(max_length=45)
    upuser_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'permission'