from django.db import models
from base.models.inmueble import Inmueble


class OtrosEspacios(models.Model):
    inmueble = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    despachos = models.PositiveIntegerField(default=0)
    vestidores = models.PositiveIntegerField(default=0)
    altillo = models.BooleanField(default=False)
    galeria = models.BooleanField(default=False)
    trastero = models.PositiveIntegerField(default=0)
    buhardilla = models.BooleanField(default=False)
    bodega = models.BooleanField(default=False)
    lavadero = models.BooleanField(default=False)
    estudios = models.PositiveIntegerField(default=0)
    bibliotecas = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} - Otros espacios'
