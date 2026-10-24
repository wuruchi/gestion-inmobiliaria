from django.db import models
from base.models.inmueble import Inmueble

class Otros(models.Model):
    modulo = models.OneToOneField(Inmueble, on_delete=models.CASCADE, null=False)
    capacidad_personas = models.IntegerField(default=0)
    suelo_piso = models.CharField(max_length=150, blank=True, null=True)
    exterior = models.CharField(max_length=150, blank=True, null=True)
    altura_real = models.CharField(max_length=150, blank=True, null=True)
    anio_ultima_reforma = models.IntegerField(blank=True, null=True)
    gastos_comunidad_incluidos = models.BooleanField(default=False)
    orientacion = models.CharField(max_length=150, blank=True, null=True)
    plazas_aparcamiento = models.IntegerField(default=0)
    chimenea = models.BooleanField(default=False)
    vistas_al_mar = models.BooleanField(default=False)
    vistas_montania = models.BooleanField(default=False)
    tipo_fachada = models.CharField(max_length=150, blank=True, null=True)
    office = models.CharField(max_length=150, blank=True, null=True)
    acepta_animales = models.BooleanField(default=False)
    estancia_minima = models.CharField(max_length=100, blank=True, null=True)
    estancia_maxima = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self) -> str:
        return f'{self.modulo.referencia} - Otros Datos'