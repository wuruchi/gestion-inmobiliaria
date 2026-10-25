from django.utils.translation.trans_real import parse_accept_lang_header
from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from .models import Inmueble, ImageInmueble, Barrio, Modalidad, Distrito, Municipio, Provincia, Caracteristicas, PlazaAparcamiento, Distribucion, Instalaciones, Dotacion, AreaRecreo, Estancias
from .models import Seguridad, Entorno, TransporteInmueble, OtrosEspacios, DescripcionInmueble
from .models import Agencia, CertificadoEnergetico, Condiciones, InclusionesAlquiler, InmuebleModalidad, MediaInmueble, RegistroLegal, RegulacionAlquiler, SolicitudReserva, TerminosAlquiler

class ProvinciasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provincia
        fields = ['id', 'codigo_ine', 'nombre', 'slug']

class MunicipiosSerializer(serializers.ModelSerializer):
    provincia = ProvinciasSerializer(read_only=True)
    class Meta:
        model = Municipio
        fields = ['id', 'codigo_ine', 'nombre', 'slug', 'provincia', 'comarca', 'latitud', 'longitud']

class MunicipiosListItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Municipio
        fields = ['id', 'codigo_ine', 'nombre', 'slug', 'provincia', 'comarca', 'latitud', 'longitud']

class DistritosSerializer(serializers.ModelSerializer):
  municipio = MunicipiosSerializer(read_only=True)
  class Meta:
    model = Distrito
    fields = ['id', 'codigo', 'nombre', 'slug', 'municipio']

class DistritosListItemSerializer(serializers.ModelSerializer):
   class Meta:
      model = Distrito
      fields = ['id', 'codigo', 'nombre', 'slug', 'municipio']

class ModalidadSerializer(serializers.ModelSerializer):
   class Meta:
      model = Modalidad
      fields = ['codigo', 'nombre', 'unidad_precio']

class BarriosSerializer(serializers.ModelSerializer):
   class Meta:
      model = Barrio
      fields = ['id', 'codigo', 'nombre', 'slug', 'distrito']

class PlazaAparcamientoSerializer(serializers.ModelSerializer):
   class Meta:
      model = PlazaAparcamiento
      fields = ['id', 'numero', 'tipo', 'superficie', 'notas', 'opcional', 'precio_opcional',
                'precio_opcional_unidad', 'precio_opcional_mas_iva', 'precio_opcional_tipo_iva']

class SingleImageSerializer(serializers.ModelSerializer):
  class Meta:
    model = ImageInmueble
    fields = ['id', 'image', 'default', 'alt_text', 'posicion', 'tipo']

class MediaInmuebleSerializer(serializers.ModelSerializer):
  class Meta:
    model = MediaInmueble
    fields = ['tipo', 'url', 'titulo']

class ImagenesMixin(serializers.Serializer):
  # Photos only: floor plans (`tipo='plano'`) are returned apart, as `planos`.
  images = serializers.SerializerMethodField()

  def _imagenes(self, obj, planos):
    # Filters the prefetched photos in Python, so it costs no extra query.
    imagenes = [i for i in obj.images.all() if (i.tipo == ImageInmueble.PLANO) == planos]
    return SingleImageSerializer(imagenes, many=True, context=self.context).data

  def get_images(self, obj):
    return self._imagenes(obj, planos=False)

class CaracteristicasSerializer(serializers.ModelSerializer):
   class Meta:
      model = Caracteristicas
      exclude = ['id', 'inmueble']  # the row of a listing: neither its own id nor the listing's is needed

class DistribucionSerializer(serializers.ModelSerializer):
   class Meta:
      model = Distribucion
      exclude = ['id', 'inmueble']  # the row of a listing: neither its own id nor the listing's is needed

class InstalacionesSerializer(serializers.ModelSerializer):
   class Meta:
      model = Instalaciones
      exclude = ['id', 'inmueble']  # the row of a listing: neither its own id nor the listing's is needed

# Supplies are rows of `Suministro`; the API flattens them back to the keys the clients know.
def instalaciones_planas(inmueble):
  try:
    datos = dict(InstalacionesSerializer(inmueble.instalaciones).data)
  except ObjectDoesNotExist:
    datos = {}
  suministros = {s.tipo: s for s in inmueble.suministros.all()}
  if not datos and not suministros:
    return None
  for tipo in ('agua', 'electricidad', 'gas'):
    s = suministros.get(tipo)
    datos[f'contador_{tipo}'] = bool(s and s.contador)
    datos[f'compania_{tipo}'] = s.compania if s else ''
  gas = suministros.get('gas')
  datos['gas'] = gas is not None
  datos['tipo_gas'] = gas.tipo_suministro if gas else ''
  return datos

class AreaRecreoSerializer(serializers.ModelSerializer):
   class Meta:
      model = AreaRecreo
      exclude = ['id', 'inmueble']  # the row of a listing: neither its own id nor the listing's is needed

class DotacionSerializer(serializers.ModelSerializer):
   class Meta:
      model = Dotacion
      exclude = ['id', 'inmueble']  # the row of a listing: neither its own id nor the listing's is needed

# The merged Estancias row is exposed under its original four keys.
class CocinaSerializer(serializers.ModelSerializer):
   class Meta:
      model = Estancias
      fields = ['cocina', 'cocina_amueblada', 'tipo_cocina', 'suelo_cocina']

class TerrazaSerializer(serializers.ModelSerializer):
   class Meta:
      model = Estancias
      fields = ['n_terrazas', 'terraza_m2', 'n_balcones', 'balcones_m2', 'descripcion']

class SalonSerializer(serializers.ModelSerializer):
   class Meta:
      model = Estancias
      fields = ['salon_m2', 'descripcion']

class CarpinteriaSerializer(serializers.ModelSerializer):
   class Meta:
      model = Estancias
      fields = ['carpinteria_interior', 'carpinteria_exterior']

class SeguridadSerializer(serializers.ModelSerializer):
   class Meta:
      model = Seguridad
      exclude = ['id', 'inmueble']  # the row of a listing: neither its own id nor the listing's is needed

class EntornoSerializer(serializers.ModelSerializer):
   class Meta:
      model = Entorno
      exclude = ['id', 'inmueble']  # the row of a listing: neither its own id nor the listing's is needed

# One row per mode in the database; the API keeps one flag and one description per mode.
def transporte_plano(inmueble):
  filas = {t.tipo: t for t in inmueble.transportes.all()}
  if not filas:
    return None
  datos = {}
  for tipo, _ in TransporteInmueble.TIPOS:
    datos[f'cerca_{tipo}'] = tipo in filas
    datos[f'descripcion_{tipo}'] = filas[tipo].descripcion if tipo in filas else ''
  return datos

class OtrosEspaciosSerializer(serializers.ModelSerializer):
   class Meta:
      model = OtrosEspacios
      exclude = ['id', 'inmueble']  # the row of a listing: neither its own id nor the listing's is needed

class CondicionesSerializer(serializers.ModelSerializer):
   class Meta:
      model = Condiciones
      exclude = ['id', 'por_defecto', 'modalidad', 'created_by', 'created_at', 'updated_by', 'updated_at']

class RegulacionAlquilerSerializer(serializers.ModelSerializer):
   class Meta:
      model = RegulacionAlquiler
      fields = ['indice_referencia_min', 'indice_referencia_max', 'indice_referencia_fecha',
                'renta_previa', 'ultima_renta', 'ultima_renta_fin']

class TerminosAlquilerSerializer(serializers.ModelSerializer):
   class Meta:
      model = TerminosAlquiler
      fields = ['acepta_animales', 'acepta_fumadores', 'uso_temporada', 'estancia_minima', 'estancia_minima_unidad',
                'estancia_maxima', 'estancia_maxima_unidad']

class InclusionesAlquilerSerializer(serializers.ModelSerializer):
   class Meta:
      model = InclusionesAlquiler
      fields = ['gastos_comunidad', 'ibi', 'seguro', 'wifi', 'suministros']

class CertificadoEnergeticoSerializer(serializers.ModelSerializer):
   class Meta:
      model = CertificadoEnergetico
      fields = ['numero', 'eficiencia', 'consumo_energetico', 'emisiones_co2', 'fecha_emision', 'fecha_vencimiento']

class RegistroLegalSerializer(serializers.ModelSerializer):
   class Meta:
      model = RegistroLegal
      fields = ['tipo', 'estado', 'numero', 'organismo']

class AgenciaSerializer(serializers.ModelSerializer):
   class Meta:
      model = Agencia
      fields = ['nombre', 'aicat', 'numero_api']

class SolicitudReservaSerializer(serializers.ModelSerializer):
   class Meta:
      model = SolicitudReserva
      fields = ['id', 'nombre', 'email', 'telefono', 'tipo', 'fecha_desde', 'mensaje', 'acepta_aviso_legal']
      read_only_fields = ['id']
      extra_kwargs = {'mensaje': {'max_length': 2000}}

   def validate_acepta_aviso_legal(self, value):
      if not value:
         raise serializers.ValidationError('Debe aceptar el aviso legal.')
      return value

# Address columns withheld when the listing asks to hide its exact location.
DIRECCION_FIELDS = ('direccion', 'direccion_short', 'dir_descripcion')

# With a hidden address the point is snapped to a grid of this many degrees (about 550 m of latitude).
PASO_COORDENADAS_OCULTAS = 0.005

def difuminar(valor):
  """Centre of the grid cell that holds the coordinate; the exact point cannot be recovered."""
  if valor is None:
    return None
  return round(round(valor / PASO_COORDENADAS_OCULTAS) * PASO_COORDENADAS_OCULTAS, 3)

class OcultarDireccionMixin(serializers.Serializer):
  def to_representation(self, instance):
    data = super().to_representation(instance)
    if instance.ocultar_direccion:
      for name in DIRECCION_FIELDS:
        if name in data:
          data[name] = ''
      for name in ('geo_latitude', 'geo_longitude'):
        if name in data:
          data[name] = difuminar(data[name])
    return data

IDIOMA_POR_DEFECTO = 'es'

def idioma_preferido(request, disponibles):
  """The best of `disponibles` for the request's `Accept-Language` (region ignored, q-values respected).

  Without a match: Spanish if there is a Spanish text, else the first available in the order of `IDIOMAS`.
  """
  cabecera = request.META.get('HTTP_ACCEPT_LANGUAGE', '') if request is not None else ''
  try:
    pedidos = parse_accept_lang_header(cabecera)
  except ValueError:  # a malformed header is ignored, not an error
    pedidos = ()
  for idioma, calidad in pedidos:
    base = idioma.split('-')[0].lower()
    if calidad > 0 and base in disponibles:
      return base
  if IDIOMA_POR_DEFECTO in disponibles:
    return IDIOMA_POR_DEFECTO
  return next((i for i, _ in DescripcionInmueble.IDIOMAS if i in disponibles), None)

class DerivedFieldsMixin(serializers.Serializer):
  instalaciones = serializers.SerializerMethodField()
  # {language code: text}, only for the languages that have a description.
  descripciones = serializers.SerializerMethodField()
  # The description in the language of `Accept-Language` ({idioma, texto}); null without descriptions.
  descripcion = serializers.SerializerMethodField()

  def get_instalaciones(self, obj):
    return instalaciones_planas(obj)

  def get_descripciones(self, obj):
    return {d.idioma: d.texto for d in obj.descripciones.all()}

  def get_descripcion(self, obj):
    textos = {d.idioma: d.texto for d in obj.descripciones.all()}
    idioma = idioma_preferido(self.context.get('request'), textos)
    return None if idioma is None else {'idioma': idioma, 'texto': textos[idioma]}

  # Zone names come from the location links, not from stored text.
  zona = serializers.SerializerMethodField()
  zona_ref = serializers.SerializerMethodField()

  def get_zona(self, obj):
    place = obj.barrio or obj.distrito
    return place.nombre if place else None

  def get_zona_ref(self, obj):
    return obj.distrito.nombre if obj.distrito else None

  # Bathroom count comes from the Distribucion table, the single source. None (unknown) without a value.
  n_banios = serializers.SerializerMethodField()

  def get_n_banios(self, obj):
    try:
      return obj.distribucion.banios
    except ObjectDoesNotExist:
      return None

# Inmueble columns shown on the public detail page.
INMUEBLE_PUBLIC_FIELDS = [
  'id', 'referencia', 'titulo', 'tipo', 'subtipo',
  'conservacion', 'anio_construccion', 'anio_ultima_reforma', 'planta', 'n_plantas', 'sup_parcela',
  'codigo_postal', 'direccion',
  'direccion_short', 'dir_descripcion', 'ocultar_direccion', 'geo_latitude', 'geo_longitude',
  'fecha_alta',
  'sup_construida', 'sup_cont_comun', 'sup_util',
  'usos',
  'gtos_comunidad', 'ibi', 'situacion_actual',
  'notas_web',
]
# Owner and internal data: never serialized publicly.
INMUEBLE_PRIVATE_FIELDS = [
  'original_id', 'publicar_web', 'fecha_baja', 'referencia_catastral',
  'fecha_entrega', 'created_at', 'updated_at', 'created_by', 'updated_by',
]
# Nested objects and computed values (declared on the serializer, not columns).
INMUEBLE_NESTED_FIELDS = [
  'n_banios', 'n_habitaciones', 'zona', 'zona_ref', 'n_plz_garaje', 'plazas', 'images', 'planos', 'medios', 'provincia', 'municipio', 'distrito', 'barrio', 'registros_legales', 'certificado_energetico',
  'caracteristicas', 'distribucion', 'instalaciones', 'arearecreo', 'dotacion',
  'cocina', 'terraza', 'salon', 'carpinteria', 'otros_espacios', 'seguridad',
  'entorno', 'transporte', 'descripciones', 'descripcion', 'gran_tenedor', 'zona_tensionada',
]

class SingleInmuebleSerializer(OcultarDireccionMixin, ImagenesMixin, DerivedFieldsMixin, serializers.ModelSerializer):
  planos = serializers.SerializerMethodField()
  medios = MediaInmuebleSerializer(many=True, read_only=True)
  provincia = ProvinciasSerializer(source='municipio.provincia', read_only=True)
  municipio = MunicipiosSerializer(read_only=True)
  distrito = DistritosSerializer(read_only=True)
  barrio = BarriosSerializer(read_only=True)
  caracteristicas = CaracteristicasSerializer(read_only=True)
  distribucion = DistribucionSerializer(read_only=True)
  arearecreo = AreaRecreoSerializer(read_only=True)
  dotacion = DotacionSerializer(read_only=True)
  cocina = CocinaSerializer(source='estancias', read_only=True)
  terraza = TerrazaSerializer(source='estancias', read_only=True)
  salon = SalonSerializer(source='estancias', read_only=True)
  carpinteria = CarpinteriaSerializer(source='estancias', read_only=True)
  otros_espacios = OtrosEspaciosSerializer(source='otrosespacios', read_only=True)
  seguridad = SeguridadSerializer(read_only=True)
  entorno = EntornoSerializer(read_only=True)
  plazas = PlazaAparcamientoSerializer(many=True, read_only=True)
  registros_legales = RegistroLegalSerializer(many=True, read_only=True)
  certificado_energetico = CertificadoEnergeticoSerializer(read_only=True)
  n_plz_garaje = serializers.SerializerMethodField()
  # True when any owner is a large holder; the owners themselves are never serialized.
  # None when no owner is recorded: unknown is not "no".
  gran_tenedor = serializers.BooleanField(read_only=True, allow_null=True)
  transporte = serializers.SerializerMethodField()

  def get_transporte(self, obj):
    return transporte_plano(obj)
  # True with a declaration in force today; None when the municipality's declarations are not loaded.
  zona_tensionada = serializers.BooleanField(read_only=True, allow_null=True)

  def get_planos(self, obj):
    return self._imagenes(obj, planos=True)

  def get_n_plz_garaje(self, obj):
    return len(obj.plazas.all())

  class Meta:
    model = Inmueble
    # Allow-list: a new Inmueble column stays private until it is added here
    # (base.tests.PublicFieldsTests fails until every column is classified).
    fields = INMUEBLE_PUBLIC_FIELDS + INMUEBLE_NESTED_FIELDS
