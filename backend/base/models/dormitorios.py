from django.db import models
from base.models.inmueble import Inmueble


class Dormitorios(models.Model):
    inmueble = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    dobles = models.PositiveIntegerField(default=0)
    individuales = models.PositiveIntegerField(default=0)
    exteriores = models.PositiveIntegerField(default=0)
    suites = models.PositiveIntegerField(default=0)

    @property
    def total(self):
        return self.dobles + self.individuales + self.suites

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} dormitorios'
