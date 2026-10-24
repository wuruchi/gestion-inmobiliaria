from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from base.models.condiciones import Condiciones
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

    mas_iva = models.BooleanField(
        default=False, verbose_name='más IVA',
        help_text='El precio no incluye el IVA.',
    )
    tipo_iva = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='tipo de IVA (%)',
        help_text='Obligatorio con "más IVA"; vacío si el precio ya lo incluye.',
    )
    condiciones = models.ForeignKey(
        Condiciones,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='precios',
        help_text='Vacío = se usan las condiciones por defecto de la modalidad.',
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
            models.CheckConstraint(
                condition=models.Q(mas_iva=False, tipo_iva__isnull=True)
                | models.Q(mas_iva=True, tipo_iva__isnull=False, tipo_iva__gte=0, tipo_iva__lte=100),
                name='inmueble_modalidad_iva_coherente',
            ),
        ]

    def clean(self):
        super().clean()
        self.validate_iva()
        self.validate_condiciones()

    def validate_iva(self):
        if self.mas_iva and self.tipo_iva is None:
            raise ValidationError({'tipo_iva': 'Indica el tipo de IVA.'})
        if not self.mas_iva and self.tipo_iva is not None:
            raise ValidationError(
                {'tipo_iva': 'Sin "más IVA" el tipo de IVA debe quedar vacío.'}
            )

    def validate_condiciones(self):
        """The conditions must be those of this modalidad."""
        if (
            self.condiciones_id
            and self.modalidad_id
            and self.condiciones.modalidad_id != self.modalidad_id
        ):
            raise ValidationError(
                {'condiciones': 'Las condiciones no son de esta modalidad.'}
            )

    def save(self, *args, **kwargs):
        self.validate_condiciones()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} {self.modalidad.nombre} {self.precio}'
