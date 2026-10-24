from django.core.exceptions import ValidationError
from django.db import models
from base.models.inmueble import Inmueble


class SolicitudReserva(models.Model):
    PENDIENTE = 'pendiente'
    CONTACTADA = 'contactada'
    CERRADA = 'cerrada'
    DESCARTADA = 'descartada'
    RESERVA = 'reserva'
    VISITA = 'visita'
    INFORMACION = 'informacion'
    TIPOS = (
        (RESERVA, 'Reserva'),
        (VISITA, 'Visita'),
        (INFORMACION, 'Información'),
    )
    ESTADOS = (
        (PENDIENTE, 'Pendiente'),
        (CONTACTADA, 'Contactada'),
        (CERRADA, 'Cerrada'),
        (DESCARTADA, 'Descartada'),
    )
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
    tipo = models.CharField(max_length=12, choices=TIPOS, default=RESERVA)
    fecha_desde = models.DateField(
        null=True, blank=True,
        help_text='Fecha deseada: de entrada en una reserva, de la visita en una visita.',
    )
    mensaje = models.TextField(blank=True, default='')
    acepta_aviso_legal = models.BooleanField(default=False)
    estado = models.CharField(max_length=12, choices=ESTADOS, default=PENDIENTE)
    datos_borrados = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
        help_text='Cuándo se vaciaron nombre, email, teléfono y mensaje (ver purgar_solicitudes).',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'solicitud'
        verbose_name_plural = 'solicitudes'

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
