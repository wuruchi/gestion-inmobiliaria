from django.db import models
from base.models.inmueble import Inmueble

class Seguridad(models.Model):
    modulo = models.OneToOneField(Inmueble, on_delete=models.CASCADE, null=False)
    portero_conserje = models.BooleanField(default=False)
    vigilancia_privada = models.BooleanField(default=False)
    camaras_seguridad = models.BooleanField(default=False)
    puerta_blindada = models.BooleanField(default=False)
    caja_seguridad = models.BooleanField(default=False)
    cristales_blindades = models.BooleanField(default=False)
    sistema_alarma = models.BooleanField(default=False)
    instalacion_antirrobo = models.BooleanField(default=False)
    instalacion_contra_incendio = models.BooleanField(default=False)
    video_portero = models.BooleanField(default=False)
    portero_automatico = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.modulo.referencia} - Seguridad'
  