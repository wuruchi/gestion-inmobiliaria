from django.core.validators import MinValueValidator
from django.db import models
from base.models.inmueble import Inmueble


class DatosInternos(models.Model):
    """Agency-only data for a listing; never serialized."""

    inmueble = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, related_name='datos_internos'
    )
    notas_internas = models.TextField(blank=True, default='')
    otros_datos = models.TextField(blank=True, default='')
    tasacion_propietario = models.DecimalField(
        max_digits=11,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='tasación del propietario',
        help_text='Valor que el propietario da al inmueble.',
    )
    fecha_tasacion = models.DateField(
        null=True, blank=True, verbose_name='fecha de la tasación',
        help_text='Cuándo dio el propietario ese valor.',
    )

    class Meta:
        verbose_name = 'datos internos'
        verbose_name_plural = 'datos internos'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(tasacion_propietario__isnull=True)
                | models.Q(tasacion_propietario__gte=0),
                name='datos_internos_tasacion_no_negativa',
            ),
            models.CheckConstraint(
                condition=models.Q(fecha_tasacion__isnull=True) | models.Q(tasacion_propietario__isnull=False),
                name='datos_internos_fecha_tasacion_con_importe',
                violation_error_message='La fecha de la tasación necesita un importe.',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} - datos internos'
