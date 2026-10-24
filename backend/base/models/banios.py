from django.db import models
from base.models.inmueble import Inmueble


class Banios(models.Model):
    inmueble = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    banios = models.PositiveIntegerField(default=0)
    suelo = models.CharField(max_length=150, blank=True, default='')

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} - Baños'
