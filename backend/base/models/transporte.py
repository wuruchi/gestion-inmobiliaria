from django.db import models
from base.models.inmueble import Inmueble


class TransporteInmueble(models.Model):
    """A public transport mode near the listing; no row means none nearby."""

    BUS = 'bus'
    METRO = 'metro'
    TRANVIA = 'tranvia'
    TREN = 'tren'
    FERROCARRIL = 'ferrocarril'
    TIPOS = [
        (BUS, 'Bus'),
        (METRO, 'Metro'),
        (TRANVIA, 'Tranvía'),
        (TREN, 'Tren'),
        (FERROCARRIL, 'Ferrocarril'),
    ]

    inmueble = models.ForeignKey(
        Inmueble, on_delete=models.CASCADE, related_name='transportes'
    )
    tipo = models.CharField(max_length=20, choices=TIPOS)
    descripcion = models.CharField(max_length=150, blank=True, default='')

    class Meta:
        verbose_name = 'transporte'
        verbose_name_plural = 'transportes'
        ordering = ['inmueble', 'tipo']
        constraints = [
            models.UniqueConstraint(
                fields=['inmueble', 'tipo'], name='uniq_transporte_inmueble_tipo'
            ),
        ]

    def __str__(self):
        return f'{self.inmueble.referencia} - {self.get_tipo_display()}'
