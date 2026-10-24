from django.db import models
from base.models.inmueble import Inmueble


class OtrosEspacios(models.Model):
    modulo = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    despachos = models.IntegerField(default=0)
    vestidores = models.IntegerField(default=0)
    altillo = models.IntegerField(default=0)
    galeria = models.IntegerField(default=0)
    trastero = models.IntegerField(default=0)
    buhardilla = models.IntegerField(default=0)
    bodega = models.IntegerField(default=0)
    lavadero = models.IntegerField(default=0)
    estudios = models.IntegerField(default=0)
    bibliotecas = models.IntegerField(default=0)

    def __str__(self) -> str:
        return f'{self.modulo.referencia} - Otros espacios'
