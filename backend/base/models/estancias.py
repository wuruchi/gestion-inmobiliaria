from django.db import models
from base.models.inmueble import Inmueble


class Estancias(models.Model):
    """Living room, terrace, kitchen and carpentry of a listing (one row each)."""

    inmueble = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    salon = models.PositiveIntegerField(default=0)
    terraza = models.PositiveIntegerField(default=0)
    balcones = models.PositiveIntegerField(default=0)
    descripcion = models.CharField(max_length=150, blank=True, default='')
    cocina = models.BooleanField(default=False)
    cocina_amueblada = models.BooleanField(default=False)
    tipo_cocina = models.CharField(max_length=150, blank=True, default='')
    suelo_cocina = models.CharField(max_length=150, blank=True, default='')
    carpinteria_interior = models.BooleanField(default=False)
    carpinteria_exterior = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'estancias'

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} - Estancias'
