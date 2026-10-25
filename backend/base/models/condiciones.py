from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from base.models.auditoria import Auditoria
from base.models.modalidad import Modalidad


class Condiciones(Auditoria):
    """Contracting conditions of a modalidad (rent or sale), as text.

    A listing picks its own record on each of its prices (`InmuebleModalidad.condiciones`);
    when empty the API uses the modalidad's default record.
    """

    nombre = models.CharField(max_length=100, unique=True)
    modalidad = models.ForeignKey(
        Modalidad, on_delete=models.PROTECT, related_name='condiciones'
    )
    por_defecto = models.BooleanField(default=False)
    # Rent and sale.
    honorarios = models.TextField(blank=True)
    itp = models.TextField(blank=True, verbose_name='ITP')
    incluido = models.TextField(blank=True, help_text='Qué incluye el precio.')
    no_incluido = models.TextField(blank=True, help_text='Qué no incluye el precio.')
    # Rent.
    fianza = models.TextField(blank=True)
    pago_adelantado = models.TextField(blank=True)
    suministros = models.TextField(blank=True)
    actualizacion_renta = models.TextField(
        blank=True, verbose_name='actualización de la renta',
        help_text='Cláusula de actualización anual, por ejemplo: IRAV. Sin pacto expreso no hay actualización.',
    )
    limpieza_final = models.TextField(blank=True)
    requisitos = models.TextField(
        blank=True, help_text='Documentación que debe aportar el inquilino o el comprador.'
    )
    # Sale: costs of buying beyond the price.
    notaria = models.TextField(blank=True, verbose_name='notaría')
    registro = models.TextField(blank=True)
    gestoria = models.TextField(blank=True, verbose_name='gestoría')
    honorarios_comprador = models.TextField(
        blank=True, help_text='Honorarios a cargo del comprador, si los hay.'
    )
    itp_porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='ITP (%)',
        help_text='Solo venta: tipo general del ITP. Vacío si se desconoce; los tipos reducidos van en el texto de ITP.',
    )
    honorarios_incluidos_en_precio = models.BooleanField(
        default=False, verbose_name='honorarios del vendedor incluidos en el precio',
        help_text='Solo venta: los honorarios de la agencia del vendedor están en el precio.',
    )

    class Meta:
        verbose_name = 'condiciones'
        verbose_name_plural = 'condiciones'
        constraints = [
            models.UniqueConstraint(
                fields=['modalidad'],
                condition=models.Q(por_defecto=True),
                name='uniq_condiciones_por_defecto_modalidad',
            ),
            models.CheckConstraint(
                condition=models.Q(itp_porcentaje__isnull=True) | models.Q(itp_porcentaje__gte=0, itp_porcentaje__lte=100),
                name='condiciones_itp_porcentaje_rango',
            ),
        ]

    def clean(self):
        super().clean()
        self.validate_solo_venta()

    def validate_solo_venta(self):
        """The ITP rate and the seller's fee belong to a sale; a rental's ITP stays in the text."""
        if (
            self.modalidad_id
            and self.modalidad.unidad_precio != 'total'
            and (self.itp_porcentaje is not None or self.honorarios_incluidos_en_precio)
        ):
            raise ValidationError('El tipo de ITP y los honorarios del vendedor solo se indican en condiciones de venta.')

    def save(self, *args, **kwargs):
        self.validate_solo_venta()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.nombre
