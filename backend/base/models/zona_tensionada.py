from django.core.exceptions import ValidationError
from django.db import models
from base.models.ubicacion import Municipio


class DeclaracionZonaTensionada(models.Model):
    """A municipality declared a stressed residential market for a period; private reference data.

    A listing is in a stressed zone when its municipality has a declaration in force on the date
    (see `Municipio.es_zona_tensionada`). Declarations start, end and are amended, hence the dates.
    """

    municipio = models.ForeignKey(
        Municipio, on_delete=models.PROTECT, related_name='declaraciones_tensionada'
    )
    desde = models.DateField(help_text='Primer día en vigor.')
    hasta = models.DateField(
        null=True, blank=True, help_text='Último día en vigor; vacío si sigue vigente.'
    )
    referencia = models.CharField(
        max_length=100, blank=True, default='',
        help_text='Resolución o publicación, por ejemplo: TER/800/2024 (DOGC 9122).',
    )

    class Meta:
        ordering = ['municipio__nombre', '-desde']
        verbose_name = 'declaración de zona tensionada'
        verbose_name_plural = 'declaraciones de zona tensionada'
        constraints = [
            models.UniqueConstraint(
                fields=['municipio', 'desde'], name='uniq_zona_tensionada_municipio_desde'
            ),
            models.CheckConstraint(
                condition=models.Q(hasta__isnull=True) | models.Q(hasta__gte=models.F('desde')),
                name='zona_tensionada_hasta_no_antes_de_desde',
            ),
        ]

    def clean(self):
        super().clean()
        if self.hasta and self.desde and self.hasta < self.desde:
            raise ValidationError({'hasta': 'La fecha final es anterior a la inicial.'})

    def en_vigor(self, fecha):
        return self.desde <= fecha and (self.hasta is None or fecha <= self.hasta)

    def __str__(self) -> str:
        return f'{self.municipio} desde {self.desde}'
