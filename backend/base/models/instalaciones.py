from django.core.exceptions import ValidationError
from django.db import models
from base.models.inmueble import Inmueble


class Instalaciones(models.Model):
    # Water, electricity and gas supplies live in `Suministro`.
    TIPOS_CALEFACCION = [('central', 'Central'), ('individual', 'Individual')]
    SUBTIPOS_CALEFACCION = [
        ('gas_natural', 'Gas natural'), ('electrica', 'Eléctrica'), ('gasoleo', 'Gasóleo'),
        ('butano_propano', 'Butano / propano'), ('biomasa', 'Biomasa'), ('aerotermia', 'Aerotermia'),
        ('solar', 'Solar'), ('otro', 'Otro'),
    ]
    inmueble = models.OneToOneField(
        Inmueble, on_delete=models.CASCADE, null=False
    )
    calefaccion = models.BooleanField(default=False)
    tipo_calefaccion = models.CharField(max_length=20, choices=TIPOS_CALEFACCION, blank=True, default='')
    subtipo_calefaccion = models.CharField(max_length=20, choices=SUBTIPOS_CALEFACCION, blank=True, default='')
    tvs = models.PositiveIntegerField(default=0)
    tv_internacional = models.BooleanField(default=False)
    antena_parabolica = models.BooleanField(default=False)
    aire_acondicionado = models.BooleanField(default=False)
    ascensor = models.PositiveIntegerField(default=0)
    internet = models.BooleanField(default=False)
    internet_velocidad_mbps = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='velocidad de internet (Mbps)',
        help_text='Velocidad contratada o disponible; vacío si se desconoce. Solo con internet.',
    )
    telefono = models.BooleanField(default=False)
    instalacion_telefono = models.BooleanField(default=False)
    dvd = models.BooleanField(default=False)
    hilo_musical = models.BooleanField(default=False)
    acceso_silla_ruedas = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(internet_velocidad_mbps__isnull=True)
                | (models.Q(internet=True) & models.Q(internet_velocidad_mbps__gt=0)),
                name='instalaciones_velocidad_con_internet',
            )
        ]

    def clean(self):
        super().clean()
        if self.internet_velocidad_mbps is not None and not self.internet:
            raise ValidationError({'internet_velocidad_mbps': 'Marca que hay internet.'})

    def __str__(self):
        return f'{self.inmueble.referencia} - Instalaciones'
