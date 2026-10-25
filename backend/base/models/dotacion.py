from django.db import models
from base.models.inmueble import Inmueble


class Dotacion(models.Model):
    inmueble = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    amueblado = models.BooleanField(default=False)
    armarios_empotrados = models.PositiveIntegerField(default=0)
    jacuzzi_hidromasaje = models.BooleanField(default=False)
    secadora = models.BooleanField(default=False)
    lavadora = models.BooleanField(default=False)
    lavavajillas = models.BooleanField(default=False)
    microondas = models.BooleanField(default=False)
    nevera = models.BooleanField(default=False)
    radio = models.BooleanField(default=False)
    ropero = models.PositiveIntegerField(default=0)
    toldo = models.BooleanField(default=False)
    horno = models.BooleanField(default=False)
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
    tendedero = models.BooleanField(default=False)
    cafetera = models.BooleanField(default=False)
    plancha = models.BooleanField(default=False, help_text='Plancha y tabla de planchar.')
    kit_limpieza = models.BooleanField(default=False)
    secador_pelo = models.BooleanField(default=False)
    papel_higienico = models.BooleanField(default=False, help_text='Papel higiénico de cortesía.')
    sofa_cama = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} - Dotación'
