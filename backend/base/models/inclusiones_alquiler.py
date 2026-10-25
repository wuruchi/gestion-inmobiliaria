from django.core.exceptions import ValidationError
from django.db import models
from base.models.inmueble_modalidad import InmuebleModalidad


class InclusionesAlquiler(models.Model):
    """What the rent of one rental offer (an `InmuebleModalidad` with a monthly price) includes.

    It belongs to the offer, not to the listing: a temporary and a habitual offer of the same dwelling
    can include different things, and a sale includes none of this. A missing row means unknown.
    The amounts (`Inmueble.gtos_comunidad`, `Inmueble.ibi`) stay on the listing. Public in the API.
    """

    oferta = models.OneToOneField(
        InmuebleModalidad, on_delete=models.CASCADE, related_name='inclusiones'
    )
    gastos_comunidad = models.BooleanField(default=False, verbose_name='gastos de comunidad')
    ibi = models.BooleanField(default=False, verbose_name='IBI')
    seguro = models.BooleanField(default=False)
    wifi = models.BooleanField(default=False)
    suministros = models.BooleanField(default=False, help_text='Agua, luz y gas.')

    class Meta:
        verbose_name = 'inclusiones del alquiler'
        verbose_name_plural = 'inclusiones del alquiler'

    def clean(self):
        super().clean()
        self.validate_oferta_de_alquiler()

    def validate_oferta_de_alquiler(self):
        """Only a rental offer (monthly price) has rent inclusions."""
        if self.oferta_id and self.oferta.modalidad.unidad_precio != 'mensual':
            raise ValidationError({'oferta': 'Solo las ofertas de alquiler tienen inclusiones de alquiler.'})

    def save(self, *args, **kwargs):
        self.validate_oferta_de_alquiler()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.oferta} - inclusiones'
