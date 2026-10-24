from django.db import models


class Modalidad(models.Model):
    """Kind of offer (temporal, habitual, venta, otros usos); loaded by seed."""

    codigo = models.SlugField(max_length=30, unique=True)
    nombre = models.CharField(max_length=100)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'codigo']
        verbose_name_plural = 'modalidades'

    def __str__(self) -> str:
        return self.nombre
