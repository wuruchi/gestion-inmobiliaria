from django.db import models
from base.models.inmueble import Inmueble


class Dormitorios(models.Model):
    modulo = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    dobles = models.IntegerField(default=0)
    individuales = models.IntegerField(default=0)
    exteriores = models.IntegerField(default=0)
    suites = models.IntegerField(default=0)

    def __str__(self) -> str:
        return f'{self.modulo.referencia} dormitorios'
