from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from base.models.inmueble import Inmueble

class Entorno(models.Model):
    inmueble = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    zona_comunitaria = models.BooleanField(default=False)
    otras_areas_comunitarias = models.BooleanField(default=False)
    jardin = models.BooleanField(default=False)
    jardin_m2 = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)], verbose_name='Jardín (m²)',
        help_text='Solo si hay jardín.',
    )
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

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(jardin_m2__isnull=True)
                | (models.Q(jardin=True) & models.Q(jardin_m2__gte=0)),
                name='entorno_jardin_m2_con_jardin',
            )
        ]

    def clean(self):
        super().clean()
        if self.jardin_m2 is not None and not self.jardin:
            raise ValidationError({'jardin_m2': 'Marca que hay jardín.'})

    def __str__(self):
        return f'{self.inmueble.referencia} - Entorno'