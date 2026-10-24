from django.core.validators import MinValueValidator
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
    # How the agency works the listing for the owner.
    exclusiva = models.BooleanField(default=False, help_text='La agencia tiene la exclusiva.')
    gestion_comercial = models.BooleanField(default=False)
    administracion = models.BooleanField(default=False)
    tasacion_propietario = models.DecimalField(
        max_digits=11,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='tasación del propietario',
        help_text='Valor que el propietario da al inmueble.',
    )

    class Meta:
        verbose_name = 'datos internos'
        verbose_name_plural = 'datos internos'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(tasacion_propietario__isnull=True)
                | models.Q(tasacion_propietario__gte=0),
                name='datos_internos_tasacion_no_negativa',
            )
        ]

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} - datos internos'
