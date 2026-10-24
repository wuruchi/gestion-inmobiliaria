from django.core.validators import MinValueValidator
from django.db import models
from base.models.inmueble import Inmueble


class HistorialRenta(models.Model):
    """Rent charged for a listing from a given date; private, never serialized."""

    inmueble = models.ForeignKey(
        Inmueble, on_delete=models.CASCADE, related_name='historial_renta'
    )
    fecha = models.DateField(help_text='Desde cuándo se cobra esta renta.')
    importe = models.DecimalField(
        max_digits=9, decimal_places=2, validators=[MinValueValidator(0)]
    )
    nota = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        ordering = ['-fecha']
        verbose_name_plural = 'historial de rentas'
        constraints = [
            models.UniqueConstraint(
                fields=['inmueble', 'fecha'], name='uniq_renta_inmueble_fecha'
            )
        ]

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} {self.fecha} {self.importe}'
