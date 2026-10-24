from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from base.models.inmueble_modalidad import InmuebleModalidad


class RegulacionAlquiler(models.Model):
    """Rent-regulation data of one rental offer (an `InmuebleModalidad` with a monthly price).

    What an ad for a habitual-residence lease in a stressed zone must show: the maximum price from the
    state reference index and the rent of the last contract of the dwelling in the last five years.
    Both come from outside (SERPAVI, the owner or the previous manager), not from our price history,
    so the last rent is declared here and has three states: `desconocida` (not confirmed yet, the
    default), `con_renta` and `sin_renta`. Public in the API; sale offers have none.
    """

    DESCONOCIDA = 'desconocida'
    CON_RENTA = 'con_renta'
    SIN_RENTA = 'sin_renta'
    RENTAS_PREVIAS = (
        (DESCONOCIDA, 'Sin confirmar'),
        (CON_RENTA, 'Hubo un alquiler en los últimos 5 años'),
        (SIN_RENTA, 'Sin alquiler en los últimos 5 años'),
    )

    oferta = models.OneToOneField(
        InmuebleModalidad, on_delete=models.CASCADE, related_name='regulacion'
    )
    indice_referencia_min = models.DecimalField(
        max_digits=9, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)], verbose_name='Índice de referencia (mínimo)',
    )
    indice_referencia_max = models.DecimalField(
        max_digits=9, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)], verbose_name='Índice de referencia (máximo)',
        help_text='Precio máximo según el sistema de índices de referencia (SERPAVI).',
    )
    indice_referencia_fecha = models.DateField(
        null=True, blank=True, verbose_name='Índice consultado el',
        help_text='El índice se actualiza con el tiempo: fecha en que se consultó.',
    )
    renta_previa = models.CharField(
        max_length=12, choices=RENTAS_PREVIAS, default=DESCONOCIDA,
        verbose_name='Alquiler en los últimos 5 años',
    )
    ultima_renta = models.DecimalField(
        max_digits=11, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)], verbose_name='Renta del último contrato',
        help_text='Solo si hubo un alquiler en los últimos 5 años.',
    )
    ultima_renta_fin = models.DateField(
        null=True, blank=True, verbose_name='Fin del último contrato',
        help_text='Para saber si sigue dentro de los 5 años.',
    )

    class Meta:
        verbose_name = 'regulación del alquiler'
        verbose_name_plural = 'regulación del alquiler'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(indice_referencia_min__isnull=True)
                | models.Q(indice_referencia_max__isnull=True)
                | models.Q(indice_referencia_min__lte=models.F('indice_referencia_max')),
                name='regulacion_indice_min_max',
            ),
            models.CheckConstraint(
                condition=models.Q(indice_referencia_min__isnull=True)
                | models.Q(indice_referencia_min__gte=0),
                name='regulacion_indice_min_no_negativo',
            ),
            models.CheckConstraint(
                condition=models.Q(indice_referencia_max__isnull=True)
                | models.Q(indice_referencia_max__gte=0),
                name='regulacion_indice_max_no_negativo',
            ),
            models.CheckConstraint(
                condition=models.Q(ultima_renta__isnull=True) | models.Q(ultima_renta__gte=0),
                name='regulacion_ultima_renta_no_negativa',
            ),
            # The amount and its end date exist exactly when there was a rental.
            models.CheckConstraint(
                condition=models.Q(renta_previa='con_renta', ultima_renta__isnull=False)
                | models.Q(
                    ~models.Q(renta_previa='con_renta'),
                    ultima_renta__isnull=True, ultima_renta_fin__isnull=True),
                name='regulacion_ultima_renta_coherente',
            ),
        ]

    def clean(self):
        super().clean()
        self.validate_renta_previa()
        self.validate_oferta_de_alquiler()
        if (
            self.indice_referencia_min is not None
            and self.indice_referencia_max is not None
            and self.indice_referencia_min > self.indice_referencia_max
        ):
            raise ValidationError({'indice_referencia_min': 'El mínimo supera al máximo.'})

    def validate_renta_previa(self):
        if self.renta_previa == self.CON_RENTA and self.ultima_renta is None:
            raise ValidationError({'ultima_renta': 'Indica la renta del último contrato.'})
        if self.renta_previa != self.CON_RENTA and (
            self.ultima_renta is not None or self.ultima_renta_fin is not None
        ):
            raise ValidationError(
                {'renta_previa': 'La renta y su fecha solo van con "hubo un alquiler".'}
            )

    def validate_oferta_de_alquiler(self):
        """Only a rental offer (monthly price) has rent regulation."""
        if self.oferta_id and self.oferta.modalidad.unidad_precio != 'mensual':
            raise ValidationError({'oferta': 'Solo las ofertas de alquiler tienen regulación.'})

    def save(self, *args, **kwargs):
        self.validate_renta_previa()
        self.validate_oferta_de_alquiler()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.oferta} - regulación'
