from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from base.models.inmueble import Inmueble
from base.models.modalidad import Modalidad


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
    # Public: a space the tenant or buyer can add for an extra price.
    opcional = models.BooleanField(default=False)
    precio_opcional = models.DecimalField(
        max_digits=11,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text='Solo si la plaza es opcional.',
    )
    precio_opcional_unidad = models.CharField(
        max_length=10, choices=Modalidad.UNIDADES_PRECIO, default=Modalidad.MENSUAL
    )
    precio_opcional_mas_iva = models.BooleanField(default=False)
    precio_opcional_tipo_iva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Obligatorio con "más IVA"; vacío si el precio ya lo incluye.',
    )

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
            models.CheckConstraint(
                condition=models.Q(precio_opcional__isnull=True) | models.Q(opcional=True),
                name='plaza_precio_solo_si_opcional',
            ),
            models.CheckConstraint(
                condition=models.Q(precio_opcional_mas_iva=False, precio_opcional_tipo_iva__isnull=True)
                | models.Q(
                    precio_opcional_mas_iva=True,
                    precio_opcional_tipo_iva__isnull=False,
                    precio_opcional_tipo_iva__gte=0,
                    precio_opcional_tipo_iva__lte=100,
                ),
                name='plaza_iva_coherente',
            ),
            models.CheckConstraint(
                condition=models.Q(precio_opcional__isnull=True) | models.Q(precio_opcional__gte=0),
                name='plaza_precio_opcional_no_negativo',
            ),
        ]

    def clean(self):
        super().clean()
        if self.precio_opcional is not None and not self.opcional:
            raise ValidationError({'precio_opcional': 'Marca la plaza como opcional.'})
        if self.precio_opcional_mas_iva and self.precio_opcional_tipo_iva is None:
            raise ValidationError({'precio_opcional_tipo_iva': 'Indica el tipo de IVA.'})
        if not self.precio_opcional_mas_iva and self.precio_opcional_tipo_iva is not None:
            raise ValidationError(
                {'precio_opcional_tipo_iva': 'Sin "más IVA" el tipo de IVA debe quedar vacío.'}
            )

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} - plaza {self.numero or self.pk}'
