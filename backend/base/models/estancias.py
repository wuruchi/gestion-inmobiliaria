from django.core.validators import MinValueValidator
from django.db import models
from base.models.inmueble import Inmueble
from base.models.opciones import MATERIALES_CARPINTERIA, MATERIALES_SUELO


SUPERFICIES = ('salon_m2', 'terraza_m2', 'balcones_m2')


def _superficie(nombre):
    return models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
        verbose_name=nombre, validators=[MinValueValidator(0)],
    )


TIPOS_COCINA = (
    ('independiente', 'Independiente'),
    ('americana', 'Americana'),
    ('abierta', 'Abierta'),
    ('office', 'Office'),
    ('otro', 'Otro'),
)


class Estancias(models.Model):
    """Living room, terrace, kitchen and carpentry of a listing (one row each)."""

    inmueble = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    salon_m2 = _superficie('Salón (m²)')
    n_terrazas = models.PositiveIntegerField(default=0, help_text='Número de terrazas.')
    terraza_m2 = _superficie('Terrazas (m²)')
    n_balcones = models.PositiveIntegerField(default=0, help_text='Número de balcones.')
    balcones_m2 = _superficie('Balcones (m²)')
    descripcion = models.CharField(max_length=150, blank=True, default='')
    cocina = models.BooleanField(default=False)
    cocina_amueblada = models.BooleanField(default=False)
    tipo_cocina = models.CharField(max_length=20, choices=TIPOS_COCINA, blank=True, default='')
    suelo_cocina = models.CharField(max_length=20, choices=MATERIALES_SUELO, blank=True, default='')
    carpinteria_interior = models.CharField(max_length=20, choices=MATERIALES_CARPINTERIA, blank=True, default='')
    carpinteria_exterior = models.CharField(max_length=20, choices=MATERIALES_CARPINTERIA, blank=True, default='')

    class Meta:
        verbose_name_plural = 'estancias'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(**{f'{name}__isnull': True})
                | models.Q(**{f'{name}__gte': 0}),
                name=f'estancias_{name}_no_negativo',
            )
            for name in SUPERFICIES
        ]

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} - Estancias'
