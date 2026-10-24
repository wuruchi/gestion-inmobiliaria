from django.db import models
from base.models.inmueble import Inmueble


class Dotacion(models.Model):
    modulo = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    amueblado = models.BooleanField(default=False)
    armarios_empotrados = models.IntegerField(default=0)
    jacuzzi_hidromasaje = models.IntegerField(default=0)
    secadora = models.IntegerField(default=0)
    lavadora = models.IntegerField(default=0)
    lavavajillas = models.IntegerField(default=0)
    microondas = models.IntegerField(default=0)
    nevera = models.IntegerField(default=0)
    radio = models.IntegerField(default=0)
    ropero = models.IntegerField(default=0)
    toldo = models.IntegerField(default=0)
    horno = models.IntegerField(default=0)
    utensilios_cocina = models.BooleanField(default=False)
    estufa = models.IntegerField(default=0)
    ventilador = models.IntegerField(default=0)
    camas = models.IntegerField(default=0)
    sofas = models.IntegerField(default=0)
    tendedero = models.IntegerField(default=0)

    def __str__(self) -> str:
        return f'{self.modulo.referencia} - Dotación'
