from django.db import models
from base.models.inmueble import Inmueble

# Create your models here.
def content_file_name(instance, filename):
    return '/'.join([str(instance.modulo._id), filename])


class ImageInmueble(models.Model):
    modulo = models.ForeignKey(
        Inmueble, related_name='images', on_delete=models.CASCADE, null=True
    )
    label = models.CharField(max_length=150, null=True, blank=True)
    image = models.FileField(
        null=True, blank=True, upload_to=content_file_name
    )
    default = models.BooleanField(null=True, blank=False, default=False)
    _id = models.AutoField(primary_key=True, editable=False)

    class Meta:
        unique_together = ('modulo', '_id')
        ordering = ['_id']
