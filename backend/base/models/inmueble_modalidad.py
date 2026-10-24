from django.core.validators import MinValueValidator
from django.db import models
from base.models.inmueble import Inmueble
from base.models.modalidad import Modalidad


class InmuebleModalidad(models.Model):
    """A modalidad offered for a listing, with its price (unit set by the modalidad)."""

    inmueble = models.ForeignKey(
        Inmueble, on_delete=models.CASCADE, related_name='precios'
    )
    modalidad = models.ForeignKey(
        Modalidad, on_delete=models.PROTECT, related_name='precios'
    )
    precio = models.DecimalField(
        max_digits=11, decimal_places=2, validators=[MinValueValidator(0)]
    )

    class Meta:
        ordering = ['modalidad__orden', 'modalidad__codigo']
        verbose_name = 'modalidad del inmueble'
        verbose_name_plural = 'modalidades del inmueble'
        constraints = [
            models.UniqueConstraint(
                fields=['inmueble', 'modalidad'], name='uniq_inmueble_modalidad'
            ),
            models.CheckConstraint(
                condition=models.Q(precio__gte=0), name='inmueble_modalidad_precio_no_negativo'
            ),
        ]

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} {self.modalidad.nombre} {self.precio}'
