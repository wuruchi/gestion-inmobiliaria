from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from base.models.inmueble import Inmueble
from base.models.propietario import Propietario


class InmueblePropietario(models.Model):
    """An owner of a listing, with their share when the listing has several; private."""

    inmueble = models.ForeignKey(
        Inmueble, on_delete=models.CASCADE, related_name='titularidades'
    )
    propietario = models.ForeignKey(
        Propietario, on_delete=models.PROTECT, related_name='titularidades'
    )
    porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='porcentaje de propiedad (%)',
        help_text='Vacío si no se conoce.',
    )

    class Meta:
        verbose_name = 'propietario del inmueble'
        verbose_name_plural = 'propietarios del inmueble'
        constraints = [
            models.UniqueConstraint(
                fields=['inmueble', 'propietario'], name='uniq_inmueble_propietario'
            ),
            models.CheckConstraint(
                condition=models.Q(porcentaje__isnull=True)
                | models.Q(porcentaje__gt=0, porcentaje__lte=100),
                name='inmueble_propietario_porcentaje_rango',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} {self.propietario}'
