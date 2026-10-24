from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Case, F, IntegerField, Value, When
from django.db.models.lookups import LessThanOrEqual
from base.models.inmueble import Inmueble

DIAS = 'dias'
MESES = 'meses'
ANIOS = 'anios'
UNIDADES_ESTANCIA = (
    (DIAS, 'Días'),
    (MESES, 'Meses'),
    (ANIOS, 'Años'),
)
# Approximate length of each unit, only to compare a minimum with a maximum.
DIAS_POR_UNIDAD = {DIAS: 1, MESES: 30, ANIOS: 365}


def _estancia_en_dias(campo):
    """SQL expression: the stay in `campo` converted to days."""
    return Case(
        *(
            When(**{f'{campo}_unidad': unidad}, then=F(campo) * Value(dias))
            for unidad, dias in DIAS_POR_UNIDAD.items()
        ),
        output_field=IntegerField(),
    )

class Otros(models.Model):
    inmueble = models.OneToOneField(Inmueble, on_delete=models.CASCADE, null=False)
    capacidad_personas = models.PositiveIntegerField(default=0)
    suelo_piso = models.CharField(max_length=150, blank=True, default='')
    exterior = models.BooleanField(default=False)
    altura_real_m = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True,
        verbose_name='Altura real (m)',
    )
    anio_ultima_reforma = models.PositiveSmallIntegerField(blank=True, null=True)
    gastos_comunidad_incluidos = models.BooleanField(default=False)
    ibi_incluido = models.BooleanField(default=False)
    orientacion = models.CharField(max_length=150, blank=True, default='')
    chimenea = models.BooleanField(default=False)
    vistas_al_mar = models.BooleanField(default=False)
    vistas_montania = models.BooleanField(default=False)
    tipo_fachada = models.CharField(max_length=150, blank=True, default='')
    office = models.CharField(max_length=150, blank=True, default='')
    acepta_animales = models.BooleanField(default=False)
    estancia_minima = models.PositiveSmallIntegerField(blank=True, null=True)
    estancia_minima_unidad = models.CharField(
        max_length=10, choices=UNIDADES_ESTANCIA, default=MESES
    )
    estancia_maxima = models.PositiveSmallIntegerField(blank=True, null=True)
    estancia_maxima_unidad = models.CharField(
        max_length=10, choices=UNIDADES_ESTANCIA, default=MESES
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(estancia_minima__isnull=True)
                | models.Q(estancia_maxima__isnull=True)
                | models.Q(LessThanOrEqual(
                    _estancia_en_dias('estancia_minima'),
                    _estancia_en_dias('estancia_maxima'),
                )),
                name='otros_estancia_min_max',
            )
        ]

    def clean(self):
        super().clean()
        if (
            self.estancia_minima is not None
            and self.estancia_maxima is not None
            and self.estancia_minima * DIAS_POR_UNIDAD[self.estancia_minima_unidad]
            > self.estancia_maxima * DIAS_POR_UNIDAD[self.estancia_maxima_unidad]
        ):
            raise ValidationError(
                {'estancia_minima': 'La estancia mínima supera a la máxima.'}
            )

    def __str__(self) -> str:
        return f'{self.inmueble.referencia} - Otros Datos'