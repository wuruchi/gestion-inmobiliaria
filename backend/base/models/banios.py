from django.db import models
from base.models.inmueble import Inmueble


class Banios(models.Model):
    modulo = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    banios = models.IntegerField(default=0)
    suelo = models.CharField(max_length=150, null=True)

    def __str__(self) -> str:
        return f'{self.modulo.referencia} - Baños'
