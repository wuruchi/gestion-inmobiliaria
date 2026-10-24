from django.db import models
from base.models.inmueble import Inmueble


class Instalaciones(models.Model):
    inmueble = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    contador_agua = models.BooleanField(default=False)
    compania_agua = models.CharField(max_length=150, blank=True, default='')
    contador_electricidad = models.BooleanField(default=False)
    compania_electricidad = models.CharField(max_length=150, blank=True, default='')
    gas = models.BooleanField(default=False)
    tipo_gas = models.CharField(max_length=150, blank=True, default='')
    contador_gas = models.BooleanField(default=False)
    compania_gas = models.CharField(max_length=150, blank=True, default='')
    calefaccion = models.BooleanField(default=False)
    tipo_calefaccion = models.CharField(max_length=150, blank=True, default='')
    subtipo_calefaccion = models.CharField(max_length=150, blank=True, default='')
    tvs = models.PositiveIntegerField(default=0)
    tv_internacional = models.BooleanField(default=False)
    antena_parabolica = models.BooleanField(default=False)
    aire_acondicionado = models.BooleanField(default=False)
    ascensor = models.PositiveIntegerField(default=0)
    internet = models.BooleanField(default=False)
    telefono = models.BooleanField(default=False)
    instalacion_telefono = models.BooleanField(default=False)
    dvd = models.BooleanField(default=False)
    hilo_musical = models.BooleanField(default=False)
    acceso_silla_ruedas = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.inmueble.referencia} - Instalaciones'
