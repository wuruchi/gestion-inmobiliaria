from django.db import models


class Modalidad(models.Model):
    """Kind of offer (temporal, habitual, venta); loaded by seed."""

    MENSUAL = 'mensual'
    TOTAL = 'total'
    UNIDADES_PRECIO = (
        (MENSUAL, 'Mensual'),
        (TOTAL, 'Total'),
    )

    codigo = models.SlugField(max_length=30, unique=True)
    nombre = models.CharField(max_length=100)
    orden = models.PositiveSmallIntegerField(default=0)
    unidad_precio = models.CharField(
        max_length=10,
        choices=UNIDADES_PRECIO,
        default=MENSUAL,
        help_text='Si el precio de esta modalidad es mensual o un importe total.',
    )

    class Meta:
        ordering = ['orden', 'codigo']
        verbose_name_plural = 'modalidades'

    def __str__(self) -> str:
        return self.nombre
