from django.core.validators import MinValueValidator
from django.db import models
from base.models.inmueble import Inmueble


class PlazaAparcamiento(models.Model):
    """A parking space that belongs to a listing (a parking space sold or let
    on its own is a listing with tipo='Parking' instead)."""

    COCHE = 'coche'
    MOTO = 'moto'
    TIPOS = (
        (COCHE, 'Coche'),
        (MOTO, 'Moto'),
    )

    inmueble = models.ForeignKey(
        Inmueble, on_delete=models.CASCADE, related_name='plazas'
    )
    numero = models.CharField(max_length=20, blank=True, default='')
    tipo = models.CharField(max_length=10, choices=TIPOS, default=COCHE)
    superficie = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Superficie (m²)',
    )
    # Private: valor and renta are never serialized.
    valor = models.DecimalField(
        max_digits=11,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    renta = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    notas = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        ordering = ['id']
        verbose_name = 'plaza de aparcamiento'
        verbose_name_plural = 'plazas de aparcamiento'
        constraints = [
            models.UniqueConstraint(
                fields=['inmueble', 'numero'],
                condition=~models.Q(numero=''),
                name='uniq_plaza_numero_por_inmueble',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} - plaza {self.numero or self.pk}'
