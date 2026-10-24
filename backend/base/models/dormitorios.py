from django.db import models
from base.models.inmueble import Inmueble


class Dormitorios(models.Model):
    inmueble = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    dobles = models.PositiveIntegerField(default=0)
    individuales = models.PositiveIntegerField(default=0)
    exteriores = models.PositiveIntegerField(default=0)
    suites = models.PositiveIntegerField(
        default=0,
        help_text='Cuántos de los dormitorios (dobles o individuales) tienen baño propio. No suma al total.',
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(suites__lte=models.F('dobles') + models.F('individuales')),
                name='dormitorios_suites_dentro_del_total',
            )
        ]

    @property
    def total(self):
        return self.dobles + self.individuales

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} dormitorios'
