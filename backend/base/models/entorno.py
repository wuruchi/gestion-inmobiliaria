from django.db import models
from base.models.inmueble import Inmueble

class Entorno(models.Model):
    inmueble = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    zona_comunitaria = models.BooleanField(default=False)
    otras_areas_comunitarias = models.BooleanField(default=False)
    jardin = models.BooleanField(default=False)
    cerca_colegios = models.BooleanField(default=False)
    cerca_farmacia = models.BooleanField(default=False)
    cerca_guarderias = models.BooleanField(default=False)
    cerca_medico = models.BooleanField(default=False)
    cerca_centro_comercial = models.BooleanField(default=False)
    distancia_playa_m = models.PositiveIntegerField(null=True, blank=True)
    distancia_poblacion_m = models.PositiveIntegerField(null=True, blank=True)
    distancia_ciudad_m = models.PositiveIntegerField(null=True, blank=True)
    cerca_supermercado = models.BooleanField(default=False)
    cerca_restaurantes = models.BooleanField(default=False)
    cerca_discotecas = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.inmueble.referencia} - Entorno'