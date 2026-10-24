from django.db import models
from base.models.inmueble import Inmueble


def content_file_name(instance, filename):
    return '/'.join([str(instance.inmueble_id), filename])


class ImageInmueble(models.Model):
    """A photo of a listing, or its floor plan (`tipo='plano'`)."""

    PLANO = 'plano'
    TIPOS = (
        ('fachada', 'Fachada'),
        ('salon', 'Salón'),
        ('cocina', 'Cocina'),
        ('dormitorio', 'Dormitorio'),
        ('banio', 'Baño'),
        ('terraza', 'Terraza'),
        ('jardin', 'Jardín'),
        ('vistas', 'Vistas'),
        (PLANO, 'Plano'),
        ('otro', 'Otro'),
    )

    inmueble = models.ForeignKey(
        Inmueble, related_name='images', on_delete=models.CASCADE
    )
    alt_text = models.CharField(max_length=150, blank=True, default='')
    image = models.ImageField(upload_to=content_file_name)
    tipo = models.CharField(max_length=20, choices=TIPOS, default='otro')
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
            ),
            # The default photo is what the listing shows first; a plan is not a photo.
            models.CheckConstraint(
                condition=~(models.Q(default=True) & models.Q(tipo='plano')),
                name='image_plano_no_es_default',
            ),
        ]
