from django.db import models
from base.models.inmueble import Inmueble


class Salon(models.Model):
    modulo = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    salon = models.IntegerField(default=0)
    descripcion = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.modulo.referencia} - Salón'
