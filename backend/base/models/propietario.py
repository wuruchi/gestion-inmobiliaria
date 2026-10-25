from django.db import models


class Propietario(models.Model):
    """Owner (person or company), independent of any listing; private, never serialized.

    A listing and its owners are linked through `InmueblePropietario`.
    """

    nombre = models.CharField(max_length=200)
    nif = models.CharField(max_length=20, blank=True, default='', help_text='Único cuando se indica.')
    email = models.EmailField(blank=True, default='')
    telefono = models.CharField(max_length=30, blank=True, default='')
    gran_tenedor = models.BooleanField(
        default=False,
        help_text='Gran tenedor según la normativa de vivienda. Se aplica a todos sus inmuebles.',
    )

    class Meta:
        ordering = ['nombre']
        verbose_name_plural = 'propietarios'
        constraints = [
            models.UniqueConstraint(
                fields=['nif'], condition=~models.Q(nif=''), name='uniq_propietario_nif',
                violation_error_message='Ya existe un propietario con este NIF.',
            )
        ]

    def __str__(self) -> str:
        return self.nombre
