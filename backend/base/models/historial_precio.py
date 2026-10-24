from django.core.validators import MinValueValidator
from django.db import models
from base.models.inmueble import Inmueble
from django.utils import timezone
from base.models.modalidad import Modalidad


class HistorialPrecio(models.Model):
    """Price of a listing under a modalidad from a given date; private, never serialized.

    `InmuebleModalidad.save()` appends a row whenever its price is created or changes, so the latest
    row always equals the current price. Rows can also be entered by hand (for example past prices).
    """

    inmueble = models.ForeignKey(
        Inmueble, on_delete=models.CASCADE, related_name='historial_precios'
    )
    modalidad = models.ForeignKey(
        Modalidad, on_delete=models.PROTECT, related_name='historial_precios'
    )
    fecha = models.DateField(help_text='Desde cuándo se cobra este precio.')
    importe = models.DecimalField(
        max_digits=11, decimal_places=2, validators=[MinValueValidator(0)]
    )
    nota = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'historial de precio'
        verbose_name_plural = 'historial de precios'
        constraints = [
            models.UniqueConstraint(
                fields=['inmueble', 'modalidad', 'fecha'],
                name='uniq_precio_inmueble_modalidad_fecha',
            )
        ]

    @classmethod
    def registrar(cls, inmueble_id, modalidad_id, importe, fecha=None):
        """Record `importe` from `fecha` (today); a second change on the same day replaces the first."""
        cls.objects.update_or_create(
            inmueble_id=inmueble_id, modalidad_id=modalidad_id,
            fecha=fecha or timezone.localdate(), defaults={'importe': importe},
        )

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} {self.modalidad} {self.fecha} {self.importe}'
