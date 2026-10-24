from django.db import models
from base.models.inmueble import Inmueble


class Carpinteria(models.Model):
    modulo = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    carpinteria_interior = models.BooleanField(default=False)
    carpinteria_exterior = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.modulo.referencia} - Carpinteria'
