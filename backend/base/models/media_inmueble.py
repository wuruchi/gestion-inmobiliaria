from django.db import models
from base.models.inmueble import Inmueble


class MediaInmueble(models.Model):
    """A video or virtual tour of a listing, by link (photos and plans are `ImageInmueble`)."""

    VIDEO = 'video'
    TOUR = 'tour'
    TIPOS = (
        (VIDEO, 'Vídeo'),
        (TOUR, 'Tour virtual'),
    )

    inmueble = models.ForeignKey(
        Inmueble, on_delete=models.CASCADE, related_name='medios'
    )
    tipo = models.CharField(max_length=10, choices=TIPOS, default=VIDEO)
    url = models.URLField(max_length=500)
    titulo = models.CharField(max_length=150, blank=True, default='')
    posicion = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['posicion', 'id']
        verbose_name = 'vídeo o tour'
        verbose_name_plural = 'vídeos y tours'
        constraints = [
            models.UniqueConstraint(
                fields=['inmueble', 'url'], name='uniq_media_url_por_inmueble'
            )
        ]

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} {self.get_tipo_display()} {self.url}'
