from django.db import models
from base.models.inmueble import Inmueble


class RegistroLegal(models.Model):
    """Registration or licence number a listing must show (AICAT, cédula, tourist licence...)."""

    AICAT = 'aicat'
    CEDULA = 'cedula_habitabilidad'
    CERTIFICADO_ENERGETICO = 'certificado_energetico'
    LICENCIA_TURISTICA = 'licencia_turistica'
    OTRO = 'otro'
    TIPOS = (
        (AICAT, 'Registro AICAT'),
        (CEDULA, 'Cédula de habitabilidad'),
        (CERTIFICADO_ENERGETICO, 'Certificado energético'),
        (LICENCIA_TURISTICA, 'Licencia turística'),
        (OTRO, 'Otro'),
    )

    inmueble = models.ForeignKey(
        Inmueble, on_delete=models.CASCADE, related_name='registros_legales'
    )
    tipo = models.CharField(max_length=30, choices=TIPOS)
    numero = models.CharField(
        max_length=60, blank=True, default='',
        help_text='Vacío si el inmueble lo tiene pero el anuncio no publica el número.',
    )
    organismo = models.CharField(
        max_length=150, blank=True, default='',
        help_text='Organismo que lo emite, por ejemplo: Generalitat de Catalunya.',
    )

    class Meta:
        ordering = ['tipo', 'numero']
        verbose_name = 'registro legal'
        verbose_name_plural = 'registros legales'
        constraints = [
            # `otro` may repeat; every other type is declared once per listing.
            models.UniqueConstraint(
                fields=['inmueble', 'tipo'],
                condition=~models.Q(tipo='otro'),
                name='uniq_registro_legal_inmueble_tipo',
            )
        ]

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} {self.get_tipo_display()} {self.numero}'
