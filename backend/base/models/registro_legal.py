from django.db import models
from base.models.inmueble import Inmueble


class RegistroLegal(models.Model):
    """Registration or licence a listing must show (cédula, NRUA, tourist licence...). The agency's AICAT is on `Agencia`."""

    CEDULA = 'cedula_habitabilidad'
    NRUA = 'nrua'
    LICENCIA_TURISTICA = 'licencia_turistica'
    OTRO = 'otro'
    TIPOS = (
        (CEDULA, 'Cédula de habitabilidad'),
        (NRUA, 'NRUA (registro único de arrendamientos)'),
        (LICENCIA_TURISTICA, 'Licencia turística'),
        (OTRO, 'Otro'),
    )

    VIGENTE = 'vigente'
    EN_TRAMITE = 'en_tramite'
    NO_APLICA = 'no_aplica'
    ESTADOS = (
        (VIGENTE, 'Vigente'),
        (EN_TRAMITE, 'En trámite'),
        (NO_APLICA, 'No aplica'),
    )

    inmueble = models.ForeignKey(
        Inmueble, on_delete=models.CASCADE, related_name='registros_legales'
    )
    tipo = models.CharField(max_length=30, choices=TIPOS)
    estado = models.CharField(
        max_length=12, choices=ESTADOS, default=VIGENTE,
        help_text='En trámite: solicitado y aún sin número. No aplica: el inmueble está exento.',
    )
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
            ),
            # A registration in process or not applicable has no number yet.
            models.CheckConstraint(
                condition=models.Q(estado='vigente') | models.Q(numero=''),
                name='registro_legal_numero_solo_vigente',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} {self.get_tipo_display()} {self.numero}'
