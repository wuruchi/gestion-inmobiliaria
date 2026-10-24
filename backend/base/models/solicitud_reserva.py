from django.core.exceptions import ValidationError
from django.db import models
from base.models.inmueble import Inmueble


class SolicitudReserva(models.Model):
    inmueble = models.ForeignKey(
        Inmueble,
        on_delete=models.SET_NULL,
        null=True,
        related_name='solicitudes',
    )
    referencia = models.CharField(
        max_length=30, editable=False, help_text='Copia de la referencia al solicitar.'
    )
    nombre = models.CharField(max_length=150)
    email = models.EmailField()
    telefono = models.CharField(max_length=30)
    fecha_desde = models.DateField(null=True, blank=True)
    acepta_aviso_legal = models.BooleanField(default=False)
    atendida = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'solicitudes de reserva'

    def clean(self):
        super().clean()
        if not self.acepta_aviso_legal:
            raise ValidationError(
                {'acepta_aviso_legal': 'Debe aceptar el aviso legal.'}
            )

    def save(self, *args, **kwargs):
        if self.inmueble_id and not self.referencia:
            self.referencia = self.inmueble.referencia
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.referencia} - {self.nombre}'
