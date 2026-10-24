from django.db import models
from base.models.inmueble import Inmueble


class Dotacion(models.Model):
    inmueble = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    amueblado = models.BooleanField(default=False)
    armarios_empotrados = models.PositiveIntegerField(default=0)
    jacuzzi_hidromasaje = models.PositiveIntegerField(default=0)
    secadora = models.PositiveIntegerField(default=0)
    lavadora = models.PositiveIntegerField(default=0)
    lavavajillas = models.PositiveIntegerField(default=0)
    microondas = models.PositiveIntegerField(default=0)
    nevera = models.PositiveIntegerField(default=0)
    radio = models.PositiveIntegerField(default=0)
    ropero = models.PositiveIntegerField(default=0)
    toldo = models.PositiveIntegerField(default=0)
    horno = models.PositiveIntegerField(default=0)
    utensilios_cocina = models.BooleanField(default=False)
    vajilla = models.BooleanField(default=False)
    cuberteria = models.BooleanField(default=False)
    cristaleria = models.BooleanField(default=False)
    ropa_cama = models.BooleanField(default=False)
    toallas = models.BooleanField(default=False)
    estufa = models.PositiveIntegerField(default=0)
    ventilador = models.PositiveIntegerField(default=0)
    camas = models.PositiveIntegerField(default=0)
    sofas = models.PositiveIntegerField(default=0)
    tendedero = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} - Dotación'
