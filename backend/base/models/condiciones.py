from django.db import models


class CondicionesAlquiler(models.Model):
    """Condiciones de contratación; un inmueble usa las suyas o las de por defecto."""

    nombre = models.CharField(max_length=100, unique=True)
    por_defecto = models.BooleanField(default=False)
    fianza = models.TextField(blank=True)
    honorarios = models.TextField(blank=True)
    pago_adelantado = models.TextField(blank=True)
    itp = models.TextField(blank=True, verbose_name='ITP')
    suministros = models.TextField(blank=True)
    limpieza_final = models.TextField(blank=True)
    incluido = models.TextField(blank=True, help_text='Qué incluye la renta.')
    no_incluido = models.TextField(blank=True, help_text='Qué no incluye la renta.')

    class Meta:
        verbose_name = 'condiciones de alquiler'
        verbose_name_plural = 'condiciones de alquiler'
        constraints = [
            models.UniqueConstraint(
                fields=['por_defecto'],
                condition=models.Q(por_defecto=True),
                name='uniq_condiciones_por_defecto',
            )
        ]

    def __str__(self) -> str:
        return self.nombre
