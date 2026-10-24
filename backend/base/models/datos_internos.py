from django.db import models
from base.models.inmueble import Inmueble
from base.models.propietario import Propietario


class DatosInternos(models.Model):
    """Agency-only data for a listing; never serialized."""

    inmueble = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, related_name='datos_internos'
    )
    propietario = models.ForeignKey(
        Propietario,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='inmuebles',
    )
    notas_internas = models.TextField(blank=True, default='')
    otros_datos = models.TextField(blank=True, default='')
    cat_nrc = models.CharField(max_length=30, blank=True, default='')
    fecha_firma = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'datos internos'
        verbose_name_plural = 'datos internos'

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} - datos internos'
