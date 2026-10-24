from django.db import models
from base.models.inmueble import Inmueble


class Cocina(models.Model):
    modulo = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    cocina = models.BooleanField(default=False)
    cocina_amueblada = models.BooleanField(default=False)
    tipo_cocina = models.CharField(max_length=150, null=True, blank=True)
    suelo_cocina = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.modulo.referencia} - Cocina'
