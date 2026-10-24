from django.db import models


class Propietario(models.Model):
    """Owner of one or more listings; private, never serialized."""

    nombre = models.CharField(max_length=200)
    nif = models.CharField(max_length=20, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    telefono = models.CharField(max_length=30, blank=True, default='')

    class Meta:
        ordering = ['nombre']
        verbose_name_plural = 'propietarios'

    def __str__(self) -> str:
        return self.nombre
