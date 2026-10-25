from django.db import models
from base.models.inmueble import Inmueble
from base.models.opciones import MATERIALES_SUELO

TIPOS_FACHADA = (
    ('ladrillo', 'Ladrillo'),
    ('piedra', 'Piedra'),
    ('hormigon', 'Hormigón'),
    ('revoco', 'Revoco'),
    ('cristal', 'Cristal'),
    ('madera', 'Madera'),
    ('metalica', 'Metálica'),
    ('otro', 'Otro'),
)


class Caracteristicas(models.Model):
    """Physical characteristics of the dwelling: floor, height, orientation, views, facade."""

    inmueble = models.OneToOneField(Inmueble, on_delete=models.CASCADE, null=False)
    suelo_piso = models.CharField(max_length=20, choices=MATERIALES_SUELO, blank=True, default='')
    exterior = models.BooleanField(default=False)
    altura_real_m = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True,
        verbose_name='Altura real (m)',
    )
    # A listing can face several directions, so there is one flag per cardinal direction.
    orientacion_norte = models.BooleanField(default=False)
    orientacion_sur = models.BooleanField(default=False)
    orientacion_este = models.BooleanField(default=False)
    orientacion_oeste = models.BooleanField(default=False)
    chimenea = models.BooleanField(default=False)
    vistas_al_mar = models.BooleanField(default=False)
    vistas_montania = models.BooleanField(default=False)
    tipo_fachada = models.CharField(max_length=20, choices=TIPOS_FACHADA, blank=True, default='')

    class Meta:
        verbose_name = 'características'
        verbose_name_plural = 'características'

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} - Características'
