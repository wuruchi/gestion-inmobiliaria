from django.db import models

from base.models.inmueble import Inmueble


class AcuerdoAdministracion(models.Model):
    """Acuerdo de Administración: what the owner entrusted to the agency, and for how long.

    Private, never serialized. A listing keeps one row per agreement, so renewals leave a history.
    """

    inmueble = models.ForeignKey(
        Inmueble, on_delete=models.CASCADE, related_name='acuerdos_administracion'
    )
    fecha_firma = models.DateField(null=True, blank=True, help_text='Vacío si se desconoce.')
    fecha_fin = models.DateField(null=True, blank=True, help_text='Vacío si sigue vigente.')
    exclusiva = models.BooleanField(default=False, help_text='La agencia tiene la exclusiva.')
    gestion_comercial = models.BooleanField(default=False)
    administracion = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha_firma', '-id']
        verbose_name = 'acuerdo de administración'
        verbose_name_plural = 'acuerdos de administración'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fecha_firma__isnull=True)
                | models.Q(fecha_fin__isnull=True)
                | models.Q(fecha_fin__gte=models.F('fecha_firma')),
                name='acuerdo_fin_no_antes_de_firma',
                violation_error_message='El acuerdo no puede terminar antes de firmarse.',
            )
        ]

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} - acuerdo de administración {self.fecha_firma or ""}'.rstrip()
