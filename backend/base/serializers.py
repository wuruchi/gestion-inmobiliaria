from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from .models import Inmueble, ImageInmueble, Barrio, Modalidad, Distrito, Municipio, Provincia, Otros, PlazaAparcamiento, Banios, Dormitorios, Instalaciones, Dotacion, AreaRecreo, Estancias
from .models import Seguridad, Entorno, Transporte, OtrosEspacios
from .models import Condiciones, InmuebleModalidad, MediaInmueble, RegistroLegal, SolicitudReserva

class ProvinciasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provincia
        fields = ['_id', 'codigo_ine', 'nombre', 'slug']

class MunicipiosSerializer(serializers.ModelSerializer):
    provincia = ProvinciasSerializer(read_only=True)
    class Meta:
        model = Municipio
        fields = ['_id', 'codigo_ine', 'nombre', 'slug', 'provincia', 'comarca', 'latitud', 'longitud']

class MunicipiosListItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Municipio
        fields = ['_id', 'codigo_ine', 'nombre', 'slug', 'provincia', 'comarca', 'latitud', 'longitud']

class DistritosSerializer(serializers.ModelSerializer):
  municipio = MunicipiosSerializer(read_only=True)
  class Meta:
    model = Distrito
    fields = ['_id', 'codigo', 'nombre', 'slug', 'municipio']

class DistritosListItemSerializer(serializers.ModelSerializer):
   class Meta:
      model = Distrito
      fields = ['_id', 'codigo', 'nombre', 'slug', 'municipio']

class ModalidadSerializer(serializers.ModelSerializer):
   class Meta:
      model = Modalidad
      fields = ['codigo', 'nombre', 'unidad_precio']

class PrecioModalidadSerializer(serializers.ModelSerializer):
   codigo = serializers.CharField(source='modalidad.codigo', read_only=True)
   nombre = serializers.CharField(source='modalidad.nombre', read_only=True)
   unidad_precio = serializers.CharField(source='modalidad.unidad_precio', read_only=True)

   class Meta:
      model = InmuebleModalidad
      fields = ['codigo', 'nombre', 'unidad_precio', 'precio', 'mas_iva', 'tipo_iva']

class BarriosSerializer(serializers.ModelSerializer):
   class Meta:
      model = Barrio
      fields = ['_id', 'codigo', 'nombre', 'slug', 'distrito']

class PlazaAparcamientoSerializer(serializers.ModelSerializer):
   class Meta:
      model = PlazaAparcamiento
      fields = ['id', 'numero', 'tipo', 'superficie', 'notas', 'opcional', 'precio_opcional',
                'precio_opcional_unidad', 'precio_opcional_mas_iva', 'precio_opcional_tipo_iva']

class SingleImageSerializer(serializers.ModelSerializer):
  class Meta:
    model = ImageInmueble
    fields = ['_id', 'image', 'default', 'alt_text', 'posicion', 'tipo']

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

class OtrosSerializer(serializers.ModelSerializer):
   class Meta:
      model = Otros
      fields = '__all__'

class BaniosSerializer(serializers.ModelSerializer):
   class Meta:
      model = Banios
      fields = '__all__'

class DormitoriosSerializer(serializers.ModelSerializer):
   class Meta:
      model = Dormitorios
      fields = '__all__'

class InstalacionesSerializer(serializers.ModelSerializer):
   class Meta:
      model = Instalaciones
      fields = '__all__'

class AreaRecreoSerializer(serializers.ModelSerializer):
   class Meta:
      model = AreaRecreo
      fields = '__all__'

class DotacionSerializer(serializers.ModelSerializer):
   class Meta:
      model = Dotacion
      fields = '__all__'

# The merged Estancias row is exposed under its original four keys.
class CocinaSerializer(serializers.ModelSerializer):
   class Meta:
      model = Estancias
      fields = ['id', 'cocina', 'cocina_amueblada', 'tipo_cocina', 'suelo_cocina', 'inmueble']

class TerrazaSerializer(serializers.ModelSerializer):
   class Meta:
      model = Estancias
      fields = ['id', 'terraza', 'terraza_m2', 'balcones', 'balcones_m2', 'descripcion', 'inmueble']

class SalonSerializer(serializers.ModelSerializer):
   class Meta:
      model = Estancias
      fields = ['id', 'salon_m2', 'descripcion', 'inmueble']

class CarpinteriaSerializer(serializers.ModelSerializer):
   class Meta:
      model = Estancias
      fields = ['id', 'carpinteria_interior', 'carpinteria_exterior', 'inmueble']

class SeguridadSerializer(serializers.ModelSerializer):
   class Meta:
      model = Seguridad
      fields = '__all__'

class EntornoSerializer(serializers.ModelSerializer):
   class Meta:
      model = Entorno
      fields = '__all__'

class TransporteSerializer(serializers.ModelSerializer):
   class Meta:
      model = Transporte
      fields = '__all__'

class OtrosEspaciosSerializer(serializers.ModelSerializer):
   class Meta:
      model = OtrosEspacios
      fields = '__all__'

class CondicionesSerializer(serializers.ModelSerializer):
   class Meta:
      model = Condiciones
      exclude = ['por_defecto', 'modalidad']

class PrecioModalidadDetalleSerializer(PrecioModalidadSerializer):
   # The listing's own conditions for this modalidad, else the modalidad's default.
   condiciones = serializers.SerializerMethodField()

   class Meta(PrecioModalidadSerializer.Meta):
      fields = PrecioModalidadSerializer.Meta.fields + ['condiciones']

   def get_condiciones(self, obj):
      if obj.condiciones_id:
         condiciones = obj.condiciones
      else:
         # One query per request, shared by every modalidad of the listing.
         if 'condiciones_por_defecto' not in self.context:
            self.context['condiciones_por_defecto'] = {
               c.modalidad_id: c for c in Condiciones.objects.filter(por_defecto=True)
            }
         defaults = self.context['condiciones_por_defecto']
         condiciones = defaults.get(obj.modalidad_id)
      return CondicionesSerializer(condiciones).data if condiciones else None

class RegistroLegalSerializer(serializers.ModelSerializer):
   class Meta:
      model = RegistroLegal
      fields = ['tipo', 'numero', 'organismo']

class SolicitudReservaSerializer(serializers.ModelSerializer):
   class Meta:
      model = SolicitudReserva
      fields = ['nombre', 'email', 'telefono', 'tipo', 'fecha_desde', 'mensaje', 'acepta_aviso_legal']
      extra_kwargs = {'mensaje': {'max_length': 2000}}

   def validate_acepta_aviso_legal(self, value):
      if not value:
         raise serializers.ValidationError('Debe aceptar el aviso legal.')
      return value

# Address columns withheld when the listing asks to hide its exact location.
DIRECCION_FIELDS = ('direccion', 'direccion_short', 'dir_descripcion')

class OcultarDireccionMixin(serializers.Serializer):
  def to_representation(self, instance):
    data = super().to_representation(instance)
    if instance.ocultar_direccion:
      for name in DIRECCION_FIELDS:
        if name in data:
          data[name] = ''
    return data

class DerivedFieldsMixin(serializers.Serializer):
  # One entry per modalidad offered, with its price and the unit of that price.
  modalidades = PrecioModalidadSerializer(source='precios', many=True, read_only=True)
  es_venta = serializers.SerializerMethodField()
  importe_alquiler = serializers.SerializerMethodField()
  importe_venta = serializers.SerializerMethodField()

  def get_es_venta(self, obj):
    # Uses the prefetched precios; kept because the frontend reads it.
    return any(p.modalidad.codigo == 'venta' for p in obj.precios.all())

  # Kept for the frontend: derived from the modalidad prices, not stored.
  def get_importe_venta(self, obj):
    prices = [p.precio for p in obj.precios.all() if p.modalidad.codigo == 'venta']
    return str(prices[0]) if prices else None

  def get_importe_alquiler(self, obj):
    prices = [p.precio for p in obj.precios.all() if p.modalidad.unidad_precio == 'mensual']
    return str(min(prices)) if prices else None

  # Zone names come from the location links, not from stored text.
  zona = serializers.SerializerMethodField()
  zona_ref = serializers.SerializerMethodField()

  def get_zona(self, obj):
    place = obj.barrio or obj.distrito
    return place.nombre if place else None

  def get_zona_ref(self, obj):
    return obj.distrito.nombre if obj.distrito else None

  # Bathroom count comes from the Banios table, the single source.
  n_banios = serializers.SerializerMethodField()

  def get_n_banios(self, obj):
    try:
      return obj.banios.banios
    except ObjectDoesNotExist:
      return 0

class InmuebleSerializer(OcultarDireccionMixin, ImagenesMixin, DerivedFieldsMixin, serializers.ModelSerializer):
  provincia = ProvinciasSerializer(source='municipio.provincia', read_only=True)
  municipio = MunicipiosSerializer(read_only=True)
  distrito = DistritosSerializer(read_only=True)
  barrio = BarriosSerializer(read_only=True)
  otros = OtrosSerializer(read_only=True)
  banios = BaniosSerializer(read_only=True)
  dormitorios = DormitoriosSerializer(read_only=True)
  instalaciones = InstalacionesSerializer(read_only=True)
  arearecreo = AreaRecreoSerializer(read_only=True)
  dotacion = DotacionSerializer(read_only=True)
  cocina = CocinaSerializer(source='estancias', read_only=True)
  terraza = TerrazaSerializer(source='estancias', read_only=True)

  class Meta:
    model = Inmueble
    fields = ['_id', 'es_venta', 'modalidades', 'referencia', 'tipo', 'subtipo', 'estado', 'sup_util', 'sup_construida',
              'importe_alquiler', 'importe_venta', 'n_habitaciones', 
              'n_banios', 'zona', 'zona_ref', 
              'descripcion_es', 'descripcion_en', 'descripcion_cat',
              'dir_descripcion', 'situacion_actual', 'fecha_disponibilidad',
              'images', 'barrio', 'distrito', 'municipio', 'provincia',
              'otros', 'banios', 'dormitorios', 'instalaciones', 'dotacion', 'arearecreo', 
              'cocina', 'terraza']



# Inmueble columns shown on the public detail page.
INMUEBLE_PUBLIC_FIELDS = [
  '_id', 'referencia', 'fecha_disponibilidad', 'titulo', 'tipo', 'subtipo',
  'conservacion', 'anio_construccion', 'planta', 'n_plantas', 'sup_parcela',
  'codigo_postal', 'direccion',
  'direccion_short', 'dir_descripcion', 'ocultar_direccion', 'geo_latitude', 'geo_longitude',
  'fecha_alta', 'estado',
  'sup_construida', 'sup_cont_comun', 'sup_util',
  'eficiencia',
  'nombre_eficiencia', 'consumo_energetico', 'emisiones_co2', 'ultima_renta',
  'indice_referencia_min', 'indice_referencia_max', 'actualizacion_renta',
  'situacion_5_anios', 'gran_tenedor', 'zona_tensionada', 'descripcion_es',
  'descripcion_en', 'descripcion_cat', 'usos',
  'gtos_comunidad', 'ibi', 'situacion_actual',
  'notas_web',
]
# Owner and internal data: never serialized publicly.
INMUEBLE_PRIVATE_FIELDS = [
  'original_id', 'publicar_web', 'fecha_baja',
  'fecha_entrega', 'created_at', 'updated_at', 'created_by', 'updated_by',
]
# Nested objects and computed values (declared on the serializer, not columns).
INMUEBLE_NESTED_FIELDS = [
  'n_banios', 'n_habitaciones', 'zona', 'zona_ref', 'modalidades', 'es_venta', 'importe_alquiler', 'importe_venta', 'n_plz_garaje', 'plazas', 'images', 'planos', 'medios', 'provincia', 'municipio', 'distrito', 'barrio', 'registros_legales',
  'otros', 'banios', 'dormitorios', 'instalaciones', 'arearecreo', 'dotacion',
  'cocina', 'terraza', 'salon', 'carpinteria', 'otros_espacios', 'seguridad',
  'entorno', 'transporte',
]

class SingleInmuebleSerializer(OcultarDireccionMixin, ImagenesMixin, DerivedFieldsMixin, serializers.ModelSerializer):
  planos = serializers.SerializerMethodField()
  medios = MediaInmuebleSerializer(many=True, read_only=True)
  provincia = ProvinciasSerializer(source='municipio.provincia', read_only=True)
  municipio = MunicipiosSerializer(read_only=True)
  distrito = DistritosSerializer(read_only=True)
  barrio = BarriosSerializer(read_only=True)
  otros = OtrosSerializer(read_only=True)
  banios = BaniosSerializer(read_only=True)
  dormitorios = DormitoriosSerializer(read_only=True)
  instalaciones = InstalacionesSerializer(read_only=True)
  arearecreo = AreaRecreoSerializer(read_only=True)
  dotacion = DotacionSerializer(read_only=True)
  cocina = CocinaSerializer(source='estancias', read_only=True)
  terraza = TerrazaSerializer(source='estancias', read_only=True)
  salon = SalonSerializer(source='estancias', read_only=True)
  carpinteria = CarpinteriaSerializer(source='estancias', read_only=True)
  otros_espacios = OtrosEspaciosSerializer(source='otrosespacios', read_only=True)
  seguridad = SeguridadSerializer(read_only=True)
  entorno = EntornoSerializer(read_only=True)
  transporte = TransporteSerializer(read_only=True)
  modalidades = PrecioModalidadDetalleSerializer(source='precios', many=True, read_only=True)
  plazas = PlazaAparcamientoSerializer(many=True, read_only=True)
  registros_legales = RegistroLegalSerializer(many=True, read_only=True)
  n_plz_garaje = serializers.SerializerMethodField()

  def get_planos(self, obj):
    return self._imagenes(obj, planos=True)

  def get_n_plz_garaje(self, obj):
    return len(obj.plazas.all())

  class Meta:
    model = Inmueble
    # Allow-list: a new Inmueble column stays private until it is added here
    # (base.tests.PublicFieldsTests fails until every column is classified).
    fields = INMUEBLE_PUBLIC_FIELDS + INMUEBLE_NESTED_FIELDS
