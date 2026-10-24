from django.core.exceptions import ValidationError
from django.db import models
from base.models.ubicacion import Provincia, Municipio, Distrito, Barrio
from base.models.condiciones import CondicionesAlquiler
from base.models.modalidad import Modalidad


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
    original_Id = models.IntegerField(null=True, blank=True, editable=False)
    referencia = models.CharField(
        max_length=30, null=False, blank=False, unique=True
    )
    fecha_disponibilidad = models.DateTimeField(null=True, blank=True)
    titulo = models.CharField(max_length=200, null=True, blank=True)
    tipo = models.CharField(
        max_length=50, null=True, blank=True, choices=TIPOS, default='Otro'
    )
    modalidades = models.ManyToManyField(
        Modalidad, blank=True, related_name='inmuebles'
    )
    poblacion = models.CharField(max_length=150, null=True, blank=True)
    ubicacion = models.CharField(max_length=150, null=True, blank=True)
    codigo_postal = models.CharField(max_length=10, null=True, blank=True)
    zona = models.CharField(max_length=200, null=True, blank=True)
    zona_ref = models.CharField(max_length=200, null=True, blank=True)
    direccion = models.CharField(max_length=200, null=False, blank=True)
    direccion_short = models.CharField(max_length=200, null=False, blank=True)
    dir_descripcion = models.TextField(null=True, blank=True)
    geo_latitude = models.FloatField(null=True)
    geo_longitude = models.FloatField(null=True)

    fecha_alta = models.DateTimeField(null=True, blank=True)
    fecha_baja = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(
        max_length=100,
        null=False,
        blank=True,
        choices=ESTADOS,
        default='Disponible',
    )
    sup_construida = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=False,
        verbose_name='Superficie Construida',
    )
    sup_cont_comun = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=False,
        verbose_name='Superficie Construida Comun',
    )
    sup_parking = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=False,
        verbose_name='Superficie Parking',
    )
    sup_util = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=False,
        verbose_name='Superficie Util',
    )
    n_plz_garaje = models.IntegerField(null=False, blank=False, default=0)
    valor_plz = models.DecimalField(max_digits=9, decimal_places=2, null=True)
    renta_plz = models.DecimalField(max_digits=9, decimal_places=2, null=True)
    cat_nrc = models.CharField(max_length=30, null=True, blank=True)
    cedula = models.CharField(max_length=20, null=True, blank=False)

    importe_alquiler = models.DecimalField(
        max_digits=9, decimal_places=2, null=True
    )
    importe_venta = models.DecimalField(
        max_digits=9, decimal_places=2, null=True
    )
    publicar_web = models.BooleanField(default=False, null=False, blank=False)

    eficiencia = models.CharField(max_length=20, null=True, blank=True)
    nombre_eficiencia = models.CharField(max_length=20, null=True, blank=True)
    consumo_energetico = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Consumo energético (kWh/m²/año)',
    )

    # Datos exigidos por la normativa de alquiler de Cataluña.
    ultima_renta = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Precio de la última renta',
    )
    indice_referencia_min = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Índice de referencia (mínimo)',
    )
    indice_referencia_max = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Índice de referencia (máximo)',
    )
    actualizacion_renta = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Actualización de renta',
        help_text='Por ejemplo: IRAV.',
    )
    situacion_5_anios = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Situación en los últimos 5 años',
    )
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

    descripcion_es = models.TextField(null=True, blank=True)
    descripcion_en = models.TextField(null=True, blank=True)
    descripcion_cat = models.TextField(null=True, blank=True)
    usos = models.TextField(null=True, blank=True)
    notas_internas = models.TextField(null=True, blank=True)
    otros_datos = models.TextField(null=True, blank=True)
    gtos_comunidad = models.DecimalField(
        max_digits=9, decimal_places=2, null=True
    )
    ibi_incluido = models.BooleanField(default=False, null=False, blank=False)
    ibi = models.DecimalField(max_digits=9, decimal_places=2, null=True)
    situacion_actual = models.CharField(max_length=100, null=True, blank=False)

    # Headline number used by the search filter; the rest of the room, bathroom
    # and equipment data lives in the one-to-one detail tables (Dormitorios,
    # Banios, Instalaciones, AreaRecreo, Otros), which are the single source.
    n_habitaciones = models.IntegerField(null=True, blank=True, default=0)
    notas_web = models.TextField(null=True, blank=True)

    fecha_firma = models.DateTimeField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)

    propietario = models.CharField(max_length=200, null=True, blank=False)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    matterport_URI = models.CharField(
        max_length=500, null=True, blank=True, default=None
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
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

    def __str__(self) -> str:
        return f'{self.referencia} {self.cat_nrc} {self.zona} {self.direccion}'
