from django.db import models
from base.models.inmueble import Inmueble

class Otros(models.Model):
    inmueble = models.OneToOneField(Inmueble, on_delete=models.CASCADE, null=False)
    capacidad_personas = models.PositiveIntegerField(default=0)
    suelo_piso = models.CharField(max_length=150, blank=True, default='')
    exterior = models.CharField(max_length=150, blank=True, default='')
    altura_real_m = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True,
        verbose_name='Altura real (m)',
    )
    anio_ultima_reforma = models.PositiveSmallIntegerField(blank=True, null=True)
    gastos_comunidad_incluidos = models.BooleanField(default=False)
    orientacion = models.CharField(max_length=150, blank=True, default='')
    chimenea = models.BooleanField(default=False)
    vistas_al_mar = models.BooleanField(default=False)
    vistas_montania = models.BooleanField(default=False)
    tipo_fachada = models.CharField(max_length=150, blank=True, default='')
    office = models.CharField(max_length=150, blank=True, default='')
    acepta_animales = models.BooleanField(default=False)
    estancia_minima_meses = models.PositiveSmallIntegerField(blank=True, null=True)
    estancia_maxima_meses = models.PositiveSmallIntegerField(blank=True, null=True)

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} - Otros Datos'