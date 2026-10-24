from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Value
from django.db.models.functions import Coalesce
from base.models.ubicacion import Provincia, Municipio, Distrito, Barrio
from base.models.condiciones import CondicionesAlquiler
from base.models.modalidad import Modalidad


# Decimal columns that cannot be negative (validator + database constraint).
NO_NEGATIVOS = (
    'sup_construida', 'sup_cont_comun', 'sup_util', 'gtos_comunidad', 'ibi',
    'ultima_renta', 'indice_referencia_min', 'indice_referencia_max',
    'consumo_energetico',
)


class InmuebleQuerySet(models.QuerySet):
    def con_habitaciones(self):
        """Annotate `habitaciones_total` (see `Inmueble.n_habitaciones`) for filtering in SQL."""
        return self.annotate(
            habitaciones_total=Coalesce(
                F('dormitorios__dobles')
                + F('dormitorios__individuales')
                + F('dormitorios__suites'),
                Value(0),
            )
        )


class Inmueble(models.Model):
    TIPOS = (
        ('Vivienda', ('Vivienda')),
        ('Oficina', ('Oficina')),
        ('Local', ('Local')),
        ('Parking', ('Parking')),
        ('Otro', ('Otro')),
    )
    ESTADOS = (
        ('Disponible', ('Disponible')),
        ('Alquilado', ('Alquilado')),
        ('Reservado', ('Reservado')),
    )
    _id = models.AutoField(primary_key=True, editable=False)
    provincia = models.ForeignKey(
        Provincia, on_delete=models.PROTECT, null=True
    )
    municipio = models.ForeignKey(
        Municipio, on_delete=models.PROTECT, null=True
    )
    distrito = models.ForeignKey(
        Distrito, on_delete=models.PROTECT, null=True
    )
    barrio = models.ForeignKey(
        Barrio, on_delete=models.PROTECT, null=True, blank=True
    )
    original_id = models.IntegerField(null=True, blank=True, editable=False)
    referencia = models.CharField(
        max_length=30, null=False, blank=False, unique=True
    )
    fecha_disponibilidad = models.DateField(null=True, blank=True)
    titulo = models.CharField(max_length=200, blank=True, default='')
    tipo = models.CharField(
        max_length=50, blank=True, choices=TIPOS, default='Otro'
    )
    modalidades = models.ManyToManyField(
        Modalidad,
        through='InmuebleModalidad',
        blank=True,
        related_name='inmuebles',
    )
    codigo_postal = models.CharField(max_length=10, blank=True, default='')
    direccion = models.CharField(max_length=200, null=False, blank=True)
    direccion_short = models.CharField(max_length=200, null=False, blank=True)
    dir_descripcion = models.TextField(blank=True, default='')
    geo_latitude = models.FloatField(null=True, blank=True)
    geo_longitude = models.FloatField(null=True, blank=True)

    fecha_alta = models.DateField(null=True, blank=True)
    fecha_baja = models.DateField(null=True, blank=True)
    estado = models.CharField(
        max_length=100,
        null=False,
        blank=True,
        choices=ESTADOS,
        default='Disponible',
    )
    sup_construida = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Superficie Construida',
        validators=[MinValueValidator(0)],
    )
    sup_cont_comun = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Superficie Construida Comun',
        validators=[MinValueValidator(0)],
    )
    sup_util = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Superficie Util',
        validators=[MinValueValidator(0)],
    )
    cedula = models.CharField(max_length=20, blank=True, default='')

    publicar_web = models.BooleanField(default=False, null=False, blank=False)

    eficiencia = models.CharField(max_length=20, blank=True, default='')
    nombre_eficiencia = models.CharField(max_length=20, blank=True, default='')
    consumo_energetico = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Consumo energético (kWh/m²/año)',
        validators=[MinValueValidator(0)],
    )

    # Datos exigidos por la normativa de alquiler de Cataluña.
    ultima_renta = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Precio de la última renta',
        validators=[MinValueValidator(0)],
    )
    indice_referencia_min = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Índice de referencia (mínimo)',
        validators=[MinValueValidator(0)],
    )
    indice_referencia_max = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Índice de referencia (máximo)',
        validators=[MinValueValidator(0)],
    )
    actualizacion_renta = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Actualización de renta',
        help_text='Por ejemplo: IRAV.', default='')
    situacion_5_anios = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Situación en los últimos 5 años', default='')
    gran_tenedor = models.BooleanField(default=False)
    zona_tensionada = models.BooleanField(
        default=False, verbose_name='Zona de mercado residencial tensionado'
    )
    condiciones = models.ForeignKey(
        CondicionesAlquiler,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='inmuebles',
        help_text='Vacío = se usan las condiciones por defecto.',
    )

    descripcion_es = models.TextField(blank=True, default='')
    descripcion_en = models.TextField(blank=True, default='')
    descripcion_cat = models.TextField(blank=True, default='')
    usos = models.TextField(blank=True, default='')
    gtos_comunidad = models.DecimalField(
        max_digits=9, decimal_places=2, null=True,
        validators=[MinValueValidator(0)], blank=True,
    )
    ibi_incluido = models.BooleanField(default=False, null=False, blank=False)
    ibi = models.DecimalField(max_digits=9, decimal_places=2, null=True, validators=[MinValueValidator(0)], blank=True)
    situacion_actual = models.CharField(max_length=100, blank=True, default='')

    # Room, bathroom and equipment data lives in the one-to-one detail tables
    # (Dormitorios, Banios, Instalaciones, AreaRecreo, Otros), the single source.
    notas_web = models.TextField(blank=True, default='')

    fecha_entrega = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name='+',
    )
    matterport_url = models.CharField(
        max_length=500, blank=True, default=''
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name='+',
    )
    updated_at = models.DateTimeField(auto_now=True)

    objects = InmuebleQuerySet.as_manager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(indice_referencia_min__isnull=True)
                | models.Q(indice_referencia_max__isnull=True)
                | models.Q(indice_referencia_min__lte=models.F('indice_referencia_max')),
                name='inmueble_indice_referencia_min_max',
            ),
            *(
                models.CheckConstraint(
                    condition=models.Q(**{f'{name}__isnull': True})
                    | models.Q(**{f'{name}__gte': 0}),
                    name=f'inmueble_{name}_no_negativo',
                )
                for name in NO_NEGATIVOS
            ),
        ]
        indexes = [
            models.Index(
                fields=['publicar_web', 'municipio', 'distrito'],
                name='inm_web_loc',
            ),
            models.Index(
                fields=['publicar_web', 'estado', 'fecha_disponibilidad'],
                name='inm_web_estado_fecha',
            ),
        ]

    def clean(self):
        super().clean()
        if (
            self.indice_referencia_min is not None
            and self.indice_referencia_max is not None
            and self.indice_referencia_min > self.indice_referencia_max
        ):
            raise ValidationError(
                {'indice_referencia_min': 'El mínimo supera al máximo.'}
            )
        if (
            self.municipio_id
            and self.provincia_id
            and self.municipio.provincia_id != self.provincia_id
        ):
            raise ValidationError(
                {'municipio': 'El municipio no pertenece a la provincia.'}
            )
        if (
            self.distrito_id
            and self.municipio_id
            and self.distrito.municipio_id != self.municipio_id
        ):
            raise ValidationError(
                {'distrito': 'El distrito no pertenece al municipio.'}
            )
        if self.barrio_id:
            if self.distrito_id and self.barrio.distrito_id != self.distrito_id:
                raise ValidationError(
                    {'barrio': 'El barrio no pertenece al distrito.'}
                )
            if (
                self.municipio_id
                and self.barrio.distrito.municipio_id != self.municipio_id
            ):
                raise ValidationError(
                    {'barrio': 'El barrio no pertenece al municipio.'}
                )

    @property
    def n_habitaciones(self):
        """Bedrooms: dobles + individuales + suites (`exteriores` is not extra rooms)."""
        total = getattr(self, 'habitaciones_total', None)
        if total is not None:
            return total
        try:
            return self.dormitorios.total
        except ObjectDoesNotExist:
            return 0

    def __str__(self) -> str:
        return f'{self.referencia} {self.direccion}'
