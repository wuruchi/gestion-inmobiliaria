from django.db import models
from base.models.inmueble import Inmueble


def content_file_name(instance, filename):
    return '/'.join([str(instance.inmueble_id), filename])


class ImageInmueble(models.Model):
    inmueble = models.ForeignKey(
        Inmueble, related_name='images', on_delete=models.CASCADE
    )
    alt_text = models.CharField(max_length=150, blank=True, default='')
    image = models.ImageField(upload_to=content_file_name)
    posicion = models.PositiveSmallIntegerField(default=0)
    default = models.BooleanField(default=False)
    _id = models.AutoField(primary_key=True, editable=False)

    class Meta:
        ordering = ['posicion', '_id']
        constraints = [
            models.UniqueConstraint(
                fields=['inmueble'],
                condition=models.Q(default=True),
                name='uniq_image_default_por_inmueble',
            )
        ]
