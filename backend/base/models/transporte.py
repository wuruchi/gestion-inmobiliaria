from django.db import models
from base.models.inmueble import Inmueble

class Transporte(models.Model):
    modulo = models.OneToOneField(Inmueble, on_delete=models.CASCADE, primary_key=True)
    cerca_bus = models.BooleanField(default=False)
    descripcion_bus = models.CharField(max_length=150, null=True, blank=True)
    cerca_metro = models.BooleanField(default=False)
    descripcion_metro = models.CharField(max_length=150, null=True, blank=True)
    cerca_tranvia = models.BooleanField(default=False)
    descripcion_tranvia = models.CharField(max_length=150, null=True, blank=True)
    cerca_tren = models.BooleanField(default=False)
    descripcion_tren = models.CharField(max_length=150, null=True, blank=True)
    cerca_ferrocarril = models.BooleanField(default=False)
    descripcion_ferrocarril = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self):
        return f'{self.modulo.referencia} - Transporte'
    