from django.db import models
from base.models.inmueble import Inmueble


class Suministro(models.Model):
    """A utility supply of the listing (water, electricity or gas); no row means none."""

    AGUA = 'agua'
    ELECTRICIDAD = 'electricidad'
    GAS = 'gas'
    TIPOS = [(AGUA, 'Agua'), (ELECTRICIDAD, 'Electricidad'), (GAS, 'Gas')]

    NATURAL = 'natural'
    BUTANO = 'butano'
    PROPANO = 'propano'
    OTRO = 'otro'
    TIPOS_GAS = [
        (NATURAL, 'Gas natural'), (BUTANO, 'Butano'), (PROPANO, 'Propano'), (OTRO, 'Otro'),
    ]

    inmueble = models.ForeignKey(
        Inmueble, on_delete=models.CASCADE, related_name='suministros'
    )
    tipo = models.CharField(max_length=20, choices=TIPOS)
    contador = models.BooleanField(default=False, help_text='Tiene contador propio.')
    compania = models.CharField(max_length=150, blank=True, default='')
    tipo_suministro = models.CharField(
        max_length=20, choices=TIPOS_GAS, blank=True, default='',
        help_text='Solo para el gas.',
    )

    class Meta:
        verbose_name = 'suministro'
        verbose_name_plural = 'suministros'
        ordering = ['inmueble', 'tipo']
        constraints = [
            models.UniqueConstraint(
                fields=['inmueble', 'tipo'], name='uniq_suministro_inmueble_tipo'
            ),
            models.CheckConstraint(
                condition=models.Q(tipo_suministro='') | models.Q(tipo='gas'),
                name='suministro_tipo_suministro_solo_gas',
            ),
        ]

    def __str__(self):
        return f'{self.inmueble.referencia} - {self.get_tipo_display()}'
