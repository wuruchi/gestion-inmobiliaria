from django.core.validators import MinValueValidator
from django.db import models

from base.models.inmueble import Inmueble


class CertificadoEnergetico(models.Model):
    """Energy performance certificate of a listing: one document, so one row.

    A certificate is valid for ten years; `fecha_vencimiento` says when this one lapses.
    """

    EFICIENCIAS = tuple((letra, letra) for letra in 'ABCDEFG')

    inmueble = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, related_name='certificado_energetico'
    )
    numero = models.CharField(
        max_length=60, blank=True, default='',
        help_text='Número de registro del certificado; vacío si el anuncio no lo publica.',
    )
    eficiencia = models.CharField(max_length=1, choices=EFICIENCIAS, blank=True, default='')
    consumo_energetico = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
        verbose_name='Consumo energético (kWh/m²/año)', validators=[MinValueValidator(0)],
    )
    emisiones_co2 = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
        verbose_name='Emisiones (kg CO₂/m²/año)', validators=[MinValueValidator(0)],
    )
    fecha_emision = models.DateField(null=True, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'certificado energético'
        verbose_name_plural = 'certificados energéticos'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(consumo_energetico__isnull=True) | models.Q(consumo_energetico__gte=0),
                name='certificado_consumo_no_negativo',
            ),
            models.CheckConstraint(
                condition=models.Q(emisiones_co2__isnull=True) | models.Q(emisiones_co2__gte=0),
                name='certificado_emisiones_no_negativas',
            ),
            models.CheckConstraint(
                condition=models.Q(fecha_emision__isnull=True)
                | models.Q(fecha_vencimiento__isnull=True)
                | models.Q(fecha_vencimiento__gte=models.F('fecha_emision')),
                name='certificado_vencimiento_no_antes_de_emision',
                violation_error_message='El certificado no puede vencer antes de emitirse.',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} - certificado energético {self.eficiencia}'.rstrip()
