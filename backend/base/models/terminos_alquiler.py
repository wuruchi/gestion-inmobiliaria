from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Case, F, IntegerField, Value, When
from django.db.models.lookups import LessThanOrEqual
from base.models.inmueble_modalidad import InmuebleModalidad

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


USOS_TEMPORADA = (
    ('ocio_vacaciones', 'Ocio / vacaciones'),
    ('trabajo', 'Trabajo'),
    ('estudios', 'Estudios'),
    ('tratamiento_medico', 'Tratamiento médico'),
    ('otro', 'Otro'),
)


class TerminosAlquiler(models.Model):
    """Terms of one rental offer (an `InmuebleModalidad` with a monthly price): stay limits and pets.

    They belong to the offer, not to the listing: a temporary and a habitual offer of the same
    dwelling have different stay limits. Sale offers have none. Public in the API.
    """

    oferta = models.OneToOneField(
        InmuebleModalidad, on_delete=models.CASCADE, related_name='terminos'
    )
    acepta_animales = models.BooleanField(default=False)
    acepta_fumadores = models.BooleanField(default=False)
    uso_temporada = models.CharField(
        max_length=20, choices=USOS_TEMPORADA, blank=True, default='',
        help_text='Solo en ofertas temporales: para qué se alquila por temporada.',
    )
    estancia_minima = models.PositiveSmallIntegerField(blank=True, null=True)
    estancia_minima_unidad = models.CharField(
        max_length=10, choices=UNIDADES_ESTANCIA, default=MESES
    )
    estancia_maxima = models.PositiveSmallIntegerField(blank=True, null=True)
    estancia_maxima_unidad = models.CharField(
        max_length=10, choices=UNIDADES_ESTANCIA, default=MESES
    )

    class Meta:
        verbose_name = 'términos del alquiler'
        verbose_name_plural = 'términos del alquiler'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(estancia_minima__isnull=True)
                | models.Q(estancia_maxima__isnull=True)
                | models.Q(LessThanOrEqual(
                    _estancia_en_dias('estancia_minima'),
                    _estancia_en_dias('estancia_maxima'),
                )),
                name='terminos_estancia_min_max',
            )
        ]

    def clean(self):
        super().clean()
        self.validate_estancia()
        self.validate_oferta_de_alquiler()
        self.validate_uso_temporada()

    def validate_estancia(self):
        if (
            self.estancia_minima is not None
            and self.estancia_maxima is not None
            and self.estancia_minima * DIAS_POR_UNIDAD[self.estancia_minima_unidad]
            > self.estancia_maxima * DIAS_POR_UNIDAD[self.estancia_maxima_unidad]
        ):
            raise ValidationError(
                {'estancia_minima': 'La estancia mínima supera a la máxima.'}
            )

    def validate_oferta_de_alquiler(self):
        """Only a rental offer (monthly price) has rental terms."""
        if self.oferta_id and self.oferta.modalidad.unidad_precio != 'mensual':
            raise ValidationError({'oferta': 'Solo las ofertas de alquiler tienen términos de alquiler.'})

    def validate_uso_temporada(self):
        """Only a temporary offer has a seasonal purpose."""
        if self.uso_temporada and self.oferta_id and self.oferta.modalidad.codigo != 'temporal':
            raise ValidationError({'uso_temporada': 'Solo las ofertas temporales tienen uso de temporada.'})

    def save(self, *args, **kwargs):
        self.validate_oferta_de_alquiler()
        self.validate_uso_temporada()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.oferta} - términos'
