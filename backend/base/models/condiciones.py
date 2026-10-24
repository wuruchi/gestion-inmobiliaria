from django.db import models
from base.models.modalidad import Modalidad


class Condiciones(models.Model):
    """Contracting conditions of a modalidad (rent or sale), as text.

    A listing picks its own record on each of its prices (`InmuebleModalidad.condiciones`);
    when empty the API uses the modalidad's default record.
    """

    nombre = models.CharField(max_length=100, unique=True)
    modalidad = models.ForeignKey(
        Modalidad, on_delete=models.PROTECT, related_name='condiciones'
    )
    por_defecto = models.BooleanField(default=False)
    # Rent and sale.
    honorarios = models.TextField(blank=True)
    itp = models.TextField(blank=True, verbose_name='ITP')
    incluido = models.TextField(blank=True, help_text='Qué incluye el precio.')
    no_incluido = models.TextField(blank=True, help_text='Qué no incluye el precio.')
    # Rent.
    fianza = models.TextField(blank=True)
    pago_adelantado = models.TextField(blank=True)
    suministros = models.TextField(blank=True)
    limpieza_final = models.TextField(blank=True)
    requisitos = models.TextField(
        blank=True, help_text='Documentación que debe aportar el inquilino o el comprador.'
    )
    # Sale: costs of buying beyond the price.
    notaria = models.TextField(blank=True, verbose_name='notaría')
    registro = models.TextField(blank=True)
    gestoria = models.TextField(blank=True, verbose_name='gestoría')
    honorarios_comprador = models.TextField(
        blank=True, help_text='Honorarios a cargo del comprador, si los hay.'
    )

    class Meta:
        verbose_name = 'condiciones'
        verbose_name_plural = 'condiciones'
        constraints = [
            models.UniqueConstraint(
                fields=['modalidad'],
                condition=models.Q(por_defecto=True),
                name='uniq_condiciones_por_defecto_modalidad',
            )
        ]

    def __str__(self) -> str:
        return self.nombre
