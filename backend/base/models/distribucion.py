from django.db import models
from base.models.inmueble import Inmueble
from base.models.opciones import MATERIALES_SUELO


class Distribucion(models.Model):
    """Bedrooms, bathrooms and capacity of a listing.

    Every count may be empty: empty means unknown, 0 means confirmed none.
    """

    inmueble = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    dobles = models.PositiveIntegerField(null=True, blank=True)
    individuales = models.PositiveIntegerField(null=True, blank=True)
    exteriores = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Cuántos de los dormitorios (dobles o individuales) dan al exterior. No suma al total.',
    )
    suites = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Cuántos de los dormitorios (dobles o individuales) tienen baño propio. No suma al total.',
    )
    banios = models.PositiveIntegerField(null=True, blank=True)
    capacidad_personas = models.PositiveIntegerField(null=True, blank=True)
    suelo_banio = models.CharField(max_length=20, choices=MATERIALES_SUELO, blank=True, default='')

    class Meta:
        verbose_name = 'distribución'
        verbose_name_plural = 'distribución'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(suites__lte=models.F('dobles') + models.F('individuales')),
                name='dormitorios_suites_dentro_del_total',
                violation_error_message='Las suites no pueden superar el total de dormitorios.',
            ),
            models.CheckConstraint(
                condition=models.Q(exteriores__lte=models.F('dobles') + models.F('individuales')),
                name='dormitorios_exteriores_dentro_del_total',
                violation_error_message='Los dormitorios exteriores no pueden superar el total.',
            ),
        ]

    @property
    def total(self):
        """Bedrooms (dobles + individuales); None when both are unknown."""
        if self.dobles is None and self.individuales is None:
            return None
        return (self.dobles or 0) + (self.individuales or 0)

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} distribución'
