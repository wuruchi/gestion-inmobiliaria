from django.db import models
from base.models.inmueble import Inmueble


class OtrosEspacios(models.Model):
    inmueble = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    despachos = models.PositiveIntegerField(default=0)
    vestidores = models.PositiveIntegerField(default=0)
    altillo = models.PositiveIntegerField(default=0)
    galeria = models.PositiveIntegerField(default=0)
    trastero = models.PositiveIntegerField(default=0)
    buhardilla = models.PositiveIntegerField(default=0)
    bodega = models.PositiveIntegerField(default=0)
    lavadero = models.PositiveIntegerField(default=0)
    estudios = models.PositiveIntegerField(default=0)
    bibliotecas = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} - Otros espacios'
