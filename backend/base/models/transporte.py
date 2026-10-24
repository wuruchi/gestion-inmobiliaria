from django.db import models
from base.models.inmueble import Inmueble

class Transporte(models.Model):
    inmueble = models.OneToOneField(Inmueble, on_delete=models.CASCADE)
    cerca_bus = models.BooleanField(default=False)
    descripcion_bus = models.CharField(max_length=150, blank=True, default='')
    cerca_metro = models.BooleanField(default=False)
    descripcion_metro = models.CharField(max_length=150, blank=True, default='')
    cerca_tranvia = models.BooleanField(default=False)
    descripcion_tranvia = models.CharField(max_length=150, blank=True, default='')
    cerca_tren = models.BooleanField(default=False)
    descripcion_tren = models.CharField(max_length=150, blank=True, default='')
    cerca_ferrocarril = models.BooleanField(default=False)
    descripcion_ferrocarril = models.CharField(max_length=150, blank=True, default='')

    def __str__(self):
        return f'{self.inmueble.referencia} - Transporte'
    