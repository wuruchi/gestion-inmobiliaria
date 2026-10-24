from django.db import models
from base.models.inmueble import Inmueble

class Entorno(models.Model):
    modulo = models.OneToOneField(
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
    distancia_playa = models.CharField(max_length=150, default=None, null=True)
    distancia_poblacion = models.CharField(max_length=150, default=None, null=True)
    distancia_ciudad = models.CharField(max_length=150, default=None, null=True)
    cerca_supermercado = models.BooleanField(default=False)
    cerca_restaurantes = models.BooleanField(default=False)
    cerca_discotecas = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.modulo.referencia} - Entorno'