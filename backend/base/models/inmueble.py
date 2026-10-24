from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Case, Exists, F, OuterRef, Value, When
from django.db.models.functions import Coalesce
from base.models.ubicacion import Municipio, Distrito, Barrio
from base.models.modalidad import Modalidad


# Decimal columns that cannot be negative (validator + database constraint).
NO_NEGATIVOS = (
    'sup_construida', 'sup_cont_comun', 'sup_util', 'gtos_comunidad', 'ibi',
    'indice_referencia_min', 'indice_referencia_max',
    'consumo_energetico', 'emisiones_co2', 'sup_parcela',
)


class InmuebleQuerySet(models.QuerySet):
    def con_habitaciones(self):
        """Annotate `habitaciones_total` (see `Inmueble.n_habitaciones`) for filtering in SQL."""
        return self.annotate(
            habitaciones_total=Coalesce(
                F('dormitorios__dobles')
                + F('dormitorios__individuales'),
                Value(0),
            )
        )

    def con_orden_estado(self):
        """Annotate `orden_estado` (see `Inmueble.estado`): 0 available, 1 reserved, 2 closed."""
        from base.models.inmueble_modalidad import InmuebleModalidad
        ofertas = InmuebleModalidad.objects.filter(inmueble=OuterRef('pk'))
        return self.annotate(
            orden_estado=Case(
                When(
                    ~Exists(ofertas)
                    | Exists(ofertas.filter(estado=InmuebleModalidad.DISPONIBLE)),
                    then=Value(0),
                ),
                When(Exists(ofertas.filter(estado=InmuebleModalidad.RESERVADO)), then=Value(1)),
                default=Value(2),
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
    # Kinds of dwelling. Only a `Vivienda` has a subtipo; the other tipos have none.
    SUBTIPOS = (
        ('piso', 'Piso'),
        ('atico', 'Ático'),
        ('duplex', 'Dúplex'),
        ('estudio', 'Estudio'),
        ('chalet_adosado', 'Chalet adosado'),
        ('chalet_independiente', 'Chalet independiente'),
        ('otro', 'Otro'),
    )
    SUBTIPOS_POR_TIPO = {'Vivienda': {codigo for codigo, _ in SUBTIPOS}}
    CONSERVACIONES = (
        ('obra_nueva', 'Obra nueva'),
        ('buen_estado', 'Buen estado'),
        ('a_reformar', 'A reformar'),
    )
    _id = models.AutoField(primary_key=True, editable=False)
    # The province is `municipio.provincia` (see the `provincia` property).
    municipio = models.ForeignKey(Municipio, on_delete=models.PROTECT)
    distrito = models.ForeignKey(
        Distrito, on_delete=models.PROTECT, null=True, blank=True
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
    subtipo = models.CharField(
        max_length=30, blank=True, choices=SUBTIPOS, default='',
        help_text='Solo para viviendas.',
    )
    conservacion = models.CharField(
        max_length=20, blank=True, choices=CONSERVACIONES, default='',
        verbose_name='Estado de conservación',
    )
    anio_construccion = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Año de construcción',
        validators=[MinValueValidator(1000), MaxValueValidator(2100)],
    )
    planta = models.SmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(-5), MaxValueValidator(100)],
        help_text='Planta del piso en el edificio: 0 es la planta baja, negativo un sótano.',
    )
    n_plantas = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Número de plantas',
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text='Plantas de la propiedad (por ejemplo, un chalet de 2 plantas).',
    )
    modalidades = models.ManyToManyField(
        Modalidad,
        through='InmuebleModalidad',
        blank=True,
        related_name='inmuebles',
    )
    propietarios = models.ManyToManyField(
        'Propietario',
        through='InmueblePropietario',
        blank=True,
        related_name='inmuebles',
    )
    codigo_postal = models.CharField(max_length=10, blank=True, default='')
    direccion = models.CharField(max_length=200, null=False, blank=True)
    direccion_short = models.CharField(max_length=200, null=False, blank=True)
    dir_descripcion = models.TextField(blank=True, default='')
    ocultar_direccion = models.BooleanField(
        default=False,
        help_text='La API no devuelve la dirección ni su descripción.',
    )
    geo_latitude = models.FloatField(null=True, blank=True)
    geo_longitude = models.FloatField(null=True, blank=True)

    fecha_alta = models.DateField(null=True, blank=True)
    fecha_baja = models.DateField(null=True, blank=True)
    sup_construida = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Superficie Construida',
        validators=[MinValueValidator(0)],
    )
    sup_parcela = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Superficie de la parcela',
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

    emisiones_co2 = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Emisiones (kg CO₂/m²/año)',
        validators=[MinValueValidator(0)],
    )
    # Datos exigidos por la normativa de alquiler de Cataluña.
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
    descripcion_es = models.TextField(blank=True, default='')
    descripcion_en = models.TextField(blank=True, default='')
    descripcion_cat = models.TextField(blank=True, default='')
    usos = models.TextField(blank=True, default='')
    gtos_comunidad = models.DecimalField(
        max_digits=9, decimal_places=2, null=True,
        validators=[MinValueValidator(0)], blank=True,
    )
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
            models.CheckConstraint(
                condition=models.Q(anio_construccion__isnull=True)
                | models.Q(anio_construccion__gte=1000, anio_construccion__lte=2100),
                name='inmueble_anio_construccion_rango',
            ),
            models.CheckConstraint(
                condition=models.Q(planta__isnull=True)
                | models.Q(planta__gte=-5, planta__lte=100),
                name='inmueble_planta_rango',
            ),
            models.CheckConstraint(
                condition=models.Q(n_plantas__isnull=True)
                | models.Q(n_plantas__gte=1, n_plantas__lte=100),
                name='inmueble_n_plantas_rango',
            ),
            models.CheckConstraint(
                condition=models.Q(subtipo='') | models.Q(tipo='Vivienda'),
                name='inmueble_subtipo_solo_vivienda',
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
                fields=['publicar_web', 'municipio', 'distrito', 'barrio'],
                name='inm_web_loc',
            ),
            models.Index(
                fields=['publicar_web', 'fecha_disponibilidad'],
                name='inm_web_fecha',
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
        self.validate_location()
        self.validate_subtipo()

    def validate_subtipo(self):
        """A subtipo only makes sense for the tipo it belongs to."""
        if self.subtipo and self.subtipo not in self.SUBTIPOS_POR_TIPO.get(self.tipo, ()):
            raise ValidationError(
                {'subtipo': 'Solo las viviendas tienen subtipo.'}
            )

    def validate_location(self):
        """The distrito must belong to the municipio and the barrio to the distrito."""
        if (
            self.distrito_id
            and self.municipio_id
            and self.distrito.municipio_id != self.municipio_id
        ):
            raise ValidationError(
                {'distrito': 'El distrito no pertenece al municipio.'}
            )
        if self.barrio_id:
            if self.distrito_id:
                if self.barrio.distrito_id != self.distrito_id:
                    raise ValidationError(
                        {'barrio': 'El barrio no pertenece al distrito.'}
                    )
            elif (
                self.municipio_id
                and self.barrio.distrito.municipio_id != self.municipio_id
            ):
                raise ValidationError(
                    {'barrio': 'El barrio no pertenece al municipio.'}
                )

    def save(self, *args, **kwargs):
        self.validate_location()
        self.validate_subtipo()
        super().save(*args, **kwargs)

    @property
    def provincia(self):
        return self.municipio.provincia

    @property
    def estado(self):
        """Availability of the listing, derived from its offers (uses prefetched `precios`).

        Disponible if any offer is available, else Reservado if any is reserved. When every offer is
        closed: Alquilado if one of them is a monthly price, else Vendido. No offers: Disponible.
        """
        ofertas = list(self.precios.all())
        estados = {o.estado for o in ofertas}
        if not ofertas or 'disponible' in estados:
            return 'Disponible'
        if 'reservado' in estados:
            return 'Reservado'
        if any(o.modalidad.unidad_precio == 'mensual' for o in ofertas):
            return 'Alquilado'
        return 'Vendido'

    @property
    def zona_tensionada(self):
        """The municipality is a stressed residential market today (uses prefetched declarations)."""
        return self.municipio.es_zona_tensionada()

    @property
    def gran_tenedor(self):
        """True when any owner of the listing is a large holder (uses prefetched `propietarios`)."""
        return any(p.gran_tenedor for p in self.propietarios.all())

    @property
    def n_habitaciones(self):
        """Bedrooms: dobles + individuales (`suites` and `exteriores` are subsets, not extra rooms)."""
        total = getattr(self, 'habitaciones_total', None)
        if total is not None:
            return total
        try:
            return self.dormitorios.total
        except ObjectDoesNotExist:
            return 0

    def __str__(self) -> str:
        return f'{self.referencia} {self.direccion}'
