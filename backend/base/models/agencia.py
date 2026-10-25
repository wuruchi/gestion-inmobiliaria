from django.db import models


class Agencia(models.Model):
    """The real-estate agency that advertises listings: its registry numbers are the agency's, not the property's."""

    nombre = models.CharField(max_length=150, unique=True)
    aicat = models.CharField(
        max_length=60, blank=True, default='',
        verbose_name='registro AICAT',
        help_text='Número de registro de la agencia (AICAT en Cataluña). Vacío si no aplica.',
    )
    numero_api = models.CharField(
        max_length=60, blank=True, default='', verbose_name='número API',
        help_text='Número de colegiado de agente de la propiedad inmobiliaria (API) de la agencia.',
    )
    direccion = models.CharField(max_length=200, blank=True, default='')
    telefono = models.CharField(max_length=30, blank=True, default='')
    email = models.EmailField(blank=True, default='')

    class Meta:
        ordering = ['nombre']
        verbose_name = 'agencia'
        verbose_name_plural = 'agencias'
        constraints = [
            # Empty means "not recorded": only filled numbers are unique.
            models.UniqueConstraint(
                fields=['aicat'], condition=~models.Q(aicat=''), name='uniq_agencia_aicat',
            ),
            models.UniqueConstraint(
                fields=['numero_api'], condition=~models.Q(numero_api=''), name='uniq_agencia_numero_api',
            ),
        ]

    def __str__(self) -> str:
        return self.nombre
