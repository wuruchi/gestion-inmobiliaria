from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.utils import timezone
from base.models.auditoria import Auditoria
from base.models.condiciones import Condiciones
from base.models.historial_precio import HistorialPrecio
from base.models.inmueble import Inmueble
from base.models.modalidad import Modalidad


class InmuebleModalidad(Auditoria):
    """A modalidad offered for a listing, with its price (unit set by the modalidad)."""

    DISPONIBLE = 'disponible'
    RESERVADO = 'reservado'
    CERRADO = 'cerrado'
    ESTADOS = (
        (DISPONIBLE, 'Disponible'),
        (RESERVADO, 'Reservado'),
        (CERRADO, 'Cerrado (alquilado o vendido)'),
    )

    inmueble = models.ForeignKey(
        Inmueble, on_delete=models.CASCADE, related_name='precios'
    )
    modalidad = models.ForeignKey(
        Modalidad, on_delete=models.PROTECT, related_name='precios'
    )
    precio = models.DecimalField(
        max_digits=11, decimal_places=2, validators=[MinValueValidator(0)]
    )

    tipo_iva = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='tipo de IVA (%)',
        help_text='Si se indica, el precio no incluye el IVA; vacío si ya lo incluye.',
    )
    fecha_disponibilidad = models.DateField(
        default=timezone.localdate, verbose_name='disponible desde',
        help_text='Desde cuándo se puede alquilar o comprar con esta oferta.',
    )
    estado = models.CharField(
        max_length=10, choices=ESTADOS, default=DISPONIBLE,
        help_text='Disponibilidad de esta oferta; la del inmueble se deduce de todas sus ofertas.',
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
                condition=models.Q(tipo_iva__isnull=True) | models.Q(tipo_iva__gte=0, tipo_iva__lte=100),
                name='inmueble_modalidad_iva_rango',
            ),
        ]

    def clean(self):
        super().clean()
        self.validate_condiciones()

    @property
    def mas_iva(self) -> bool:
        """The price excludes VAT: derived from `tipo_iva`, which is set only then."""
        return self.tipo_iva is not None

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
        """Saving a new or changed price also appends it to `HistorialPrecio`.

        `QuerySet.update()` and `bulk_create()` skip this; change prices through `save()`.
        """
        self.validate_condiciones()
        update_fields = kwargs.get('update_fields')
        toca_precio = update_fields is None or 'precio' in update_fields
        anterior = None
        if self.pk and toca_precio:
            anterior = type(self).objects.filter(pk=self.pk).values_list('precio', flat=True).first()
        with transaction.atomic():
            super().save(*args, **kwargs)
            if toca_precio and (anterior is None or anterior != Decimal(str(self.precio))):
                HistorialPrecio.registrar(self.inmueble_id, self.modalidad_id, self.precio)

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} {self.modalidad.nombre} {self.precio}'
