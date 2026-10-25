from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Case, Exists, F, IntegerField, OuterRef, Subquery, Value, When
from django.db.models.functions import Coalesce
from base.models.ubicacion import Municipio, Distrito, Barrio
from base.models.modalidad import Modalidad


# Decimal columns that cannot be negative (validator + database constraint).
NO_NEGATIVOS = (
    'sup_construida', 'sup_cont_comun', 'sup_util', 'gtos_comunidad', 'ibi',
    'sup_parcela',
)


class InmuebleQuerySet(models.QuerySet):
    def con_habitaciones(self):
        """Annotate `habitaciones_total` (see `Inmueble.n_habitaciones`) for filtering in SQL."""
        dobles, individuales = F('distribucion__dobles'), F('distribucion__individuales')
        return self.annotate(
            habitaciones_total=Case(
                When(distribucion__dobles__isnull=True, distribucion__individuales__isnull=True, then=Value(None)),
                default=Coalesce(dobles, Value(0)) + Coalesce(individuales, Value(0)),
                output_field=IntegerField(),
            )
        )

    def con_disponibilidad(self):
        """Annotate `proxima_disponibilidad` (see `Inmueble.fecha_disponibilidad`) for ordering in SQL."""
        from base.models.inmueble_modalidad import InmuebleModalidad
        abiertas = (
            InmuebleModalidad.objects.filter(inmueble=OuterRef('pk'))
            .exclude(estado=InmuebleModalidad.CERRADO)
            .order_by('fecha_disponibilidad')
        )
        return self.annotate(proxima_disponibilidad=Subquery(abiertas.values('fecha_disponibilidad')[:1]))

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
        ('vivienda', 'Vivienda'),
        ('oficina', 'Oficina'),
        ('local', 'Local'),
        ('parking', 'Parking'),
        ('terreno', 'Terreno'),
        ('trastero', 'Trastero'),
        ('edificio', 'Edificio'),
        ('nave', 'Nave'),
        ('otro', 'Otro'),
    )
    # Kinds of dwelling. Only a `Vivienda` has a subtipo; the other tipos have none.
    SUBTIPOS = (
        ('piso', 'Piso'),
        ('atico', 'Ático'),
        ('duplex', 'Dúplex'),
        ('estudio', 'Estudio'),
        ('loft', 'Loft'),
        ('planta_baja', 'Planta baja'),
        ('chalet_adosado', 'Chalet adosado'),
        ('chalet_pareado', 'Chalet pareado'),
        ('chalet_independiente', 'Chalet independiente'),
        ('casa_pueblo', 'Casa de pueblo'),
        ('masia', 'Masía'),
        ('otro', 'Otro'),
    )
    SUBTIPOS_POR_TIPO = {'vivienda': {codigo for codigo, _ in SUBTIPOS}}
    SITUACIONES = (
        ('libre', 'Libre'),
        ('ocupado', 'Ocupado'),
        ('alquilado', 'Alquilado'),
        ('alquiler_vacacional', 'Alquiler vacacional'),
        ('otro', 'Otro'),
    )
    CONSERVACIONES = (
        ('obra_nueva', 'Obra nueva'),
        ('reformado', 'Reformado'),
        ('buen_estado', 'Buen estado'),
        ('a_reformar', 'A reformar'),
    )
    id = models.AutoField(primary_key=True, editable=False)
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
    titulo = models.CharField(max_length=200, blank=True, default='')
    tipo = models.CharField(
        max_length=50, blank=True, choices=TIPOS, default='otro'
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
    anio_ultima_reforma = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Año de la última reforma',
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
    direccion_short = models.CharField(
        max_length=200, null=False, blank=True, verbose_name='dirección corta',
        help_text='Forma abreviada que se muestra en listados. La escribe el personal; no se calcula de la dirección.',
    )
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

    # Private: identifies the property for the agency, so it is not in the public allow-list.
    referencia_catastral = models.CharField(max_length=30, blank=True, default='')
    usos = models.TextField(blank=True, default='')
    gtos_comunidad = models.DecimalField(
        max_digits=9, decimal_places=2, null=True,
        validators=[MinValueValidator(0)], blank=True,
    )
    ibi = models.DecimalField(max_digits=9, decimal_places=2, null=True, validators=[MinValueValidator(0)], blank=True)
    gastos_comunidad_incluidos = models.BooleanField(default=False)
    ibi_incluido = models.BooleanField(default=False)
    situacion_actual = models.CharField(max_length=20, choices=SITUACIONES, blank=True, default='')

    # Room, bathroom and equipment data lives in the one-to-one detail tables
    # (Distribucion, Instalaciones, AreaRecreo, Caracteristicas), the single source.
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
                condition=models.Q(anio_construccion__isnull=True)
                | models.Q(anio_construccion__gte=1000, anio_construccion__lte=2100),
                name='inmueble_anio_construccion_rango',
            ),
            models.CheckConstraint(
                condition=models.Q(anio_ultima_reforma__isnull=True)
                | models.Q(anio_ultima_reforma__gte=1000, anio_ultima_reforma__lte=2100),
                name='inmueble_anio_ultima_reforma_rango',
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
                condition=models.Q(sup_util__isnull=True) | models.Q(sup_construida__isnull=True)
                | models.Q(sup_util__lte=models.F('sup_construida')),
                name='inmueble_sup_util_no_supera_construida',
                violation_error_message='La superficie útil no puede superar la construida.',
            ),
            models.CheckConstraint(
                condition=models.Q(fecha_alta__isnull=True) | models.Q(fecha_baja__isnull=True)
                | models.Q(fecha_baja__gte=models.F('fecha_alta')),
                name='inmueble_fecha_baja_no_antes_de_alta',
                violation_error_message='La fecha de baja no puede ser anterior a la de alta.',
            ),
            models.CheckConstraint(
                condition=models.Q(subtipo='') | models.Q(tipo='vivienda'),
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
        ]

    def clean(self):
        super().clean()
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
    def fecha_disponibilidad(self):
        """Earliest availability date among the offers that are not closed (uses prefetched `precios`).

        A closed offer (rented or sold) says nothing about when the listing can be taken, so it is ignored.
        None when every offer is closed, or there are none.
        """
        fechas = [o.fecha_disponibilidad for o in self.precios.all() if o.estado != 'cerrado']
        return min(fechas) if fechas else None

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
        """Bedrooms: dobles + individuales (`suites` and `exteriores` are subsets, not extra rooms).

        None when the layout is unknown (no `Distribucion` row, or both counts empty), not zero.
        """
        if hasattr(self, 'habitaciones_total'):
            return self.habitaciones_total
        try:
            return self.distribucion.total
        except ObjectDoesNotExist:
            return None

    def __str__(self) -> str:
        return f'{self.referencia} {self.direccion}'
