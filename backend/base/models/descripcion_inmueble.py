from django.db import models
from base.models.inmueble import Inmueble


class DescripcionInmueble(models.Model):
    """The public description of a listing in one language."""

    ES = 'es'
    EN = 'en'
    CA = 'ca'
    IDIOMAS = [(ES, 'Español'), (EN, 'English'), (CA, 'Català')]

    inmueble = models.ForeignKey(
        Inmueble, on_delete=models.CASCADE, related_name='descripciones'
    )
    idioma = models.CharField(max_length=2, choices=IDIOMAS)
    texto = models.TextField()

    class Meta:
        verbose_name = 'descripción'
        verbose_name_plural = 'descripciones'
        ordering = ['inmueble', 'idioma']
        constraints = [
            models.UniqueConstraint(
                fields=['inmueble', 'idioma'], name='uniq_descripcion_inmueble_idioma'
            ),
        ]

    def __str__(self):
        return f'{self.inmueble.referencia} - {self.idioma}'
