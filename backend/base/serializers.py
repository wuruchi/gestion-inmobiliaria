from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from .models import Inmueble, ImageInmueble, Barrio, Modalidad, Distrito, Municipio, Provincia, Otros, Banios, Dormitorios, Instalaciones, Dotacion, AreaRecreo, Cocina, Terraza
from .models import Seguridad, Entorno, Transporte, Salon, Carpinteria, OtrosEspacios
from .models import CondicionesAlquiler, SolicitudReserva

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
      fields = ['codigo', 'nombre']

class BarriosSerializer(serializers.ModelSerializer):
   class Meta:
      model = Barrio
      fields = ['_id', 'codigo', 'nombre', 'slug', 'distrito']

class SingleImageSerializer(serializers.ModelSerializer):
  class Meta:
    model = ImageInmueble
    fields = ['_id', 'image', 'default']

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

class CocinaSerializer(serializers.ModelSerializer):
   class Meta:
      model = Cocina
      fields = '__all__'

class TerrazaSerializer(serializers.ModelSerializer):
   class Meta:
      model = Terraza
      fields = '__all__'

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

class SalonSerializer(serializers.ModelSerializer):
   class Meta:
      model = Salon
      fields = '__all__'

class CarpinteriaSerializer(serializers.ModelSerializer):
   class Meta:
      model = Carpinteria
      fields = '__all__'

class OtrosEspaciosSerializer(serializers.ModelSerializer):
   class Meta:
      model = OtrosEspacios
      fields = '__all__'

class CondicionesAlquilerSerializer(serializers.ModelSerializer):
   class Meta:
      model = CondicionesAlquiler
      exclude = ['por_defecto']

class SolicitudReservaSerializer(serializers.ModelSerializer):
   class Meta:
      model = SolicitudReserva
      fields = ['nombre', 'email', 'telefono', 'fecha_desde', 'acepta_aviso_legal']

   def validate_acepta_aviso_legal(self, value):
      if not value:
         raise serializers.ValidationError('Debe aceptar el aviso legal.')
      return value

class DerivedFieldsMixin(serializers.Serializer):
  modalidades = ModalidadSerializer(many=True, read_only=True)
  es_venta = serializers.SerializerMethodField()

  def get_es_venta(self, obj):
    # Uses the prefetched modalidades; kept because the frontend reads it.
    return any(m.codigo == 'venta' for m in obj.modalidades.all())


  # Bathroom count comes from the Banios table, the single source.
  n_banyos = serializers.SerializerMethodField()

  def get_n_banyos(self, obj):
    try:
      return obj.banios.banios
    except ObjectDoesNotExist:
      return 0

class InmuebleSerializer(DerivedFieldsMixin, serializers.ModelSerializer):
  images = SingleImageSerializer(many=True, read_only=True)
  provincia = ProvinciasSerializer(read_only=True)
  municipio = MunicipiosSerializer(read_only=True)
  distrito = DistritosSerializer(read_only=True)
  barrio = BarriosSerializer(read_only=True)
  otros = OtrosSerializer(read_only=True)
  banios = BaniosSerializer(read_only=True)
  dormitorios = DormitoriosSerializer(read_only=True)
  instalaciones = InstalacionesSerializer(read_only=True)
  arearecreo = AreaRecreoSerializer(read_only=True)
  dotacion = DotacionSerializer(read_only=True)
  cocina = CocinaSerializer(read_only=True)
  terraza = TerrazaSerializer(read_only=True)

  class Meta:
    model = Inmueble
    fields = ['_id', 'es_venta', 'modalidades', 'referencia', 'tipo', 'estado', 'sup_util', 'cedula', 
              'importe_alquiler', 'importe_venta', 'n_habitaciones', 
              'n_banyos', 'zona', 'zona_ref', 
              'descripcion_es', 'descripcion_en', 'descripcion_cat',
              'dir_descripcion', 'situacion_actual', 'fecha_disponibilidad',
              'images', 'barrio', 'distrito', 'municipio', 'provincia',
              'otros', 'banios', 'dormitorios', 'instalaciones', 'dotacion', 'arearecreo', 
              'cocina', 'terraza']



# Inmueble columns shown on the public detail page.
INMUEBLE_PUBLIC_FIELDS = [
  '_id', 'referencia', 'fecha_disponibilidad', 'titulo', 'tipo',
  'poblacion', 'ubicacion', 'codigo_postal', 'zona', 'zona_ref', 'direccion',
  'direccion_short', 'dir_descripcion', 'geo_latitude', 'geo_longitude',
  'fecha_alta', 'estado',
  'sup_construida', 'sup_cont_comun', 'sup_parking', 'sup_util', 'n_plz_garaje',
  'cedula', 'importe_alquiler', 'importe_venta', 'eficiencia',
  'nombre_eficiencia', 'consumo_energetico', 'ultima_renta',
  'indice_referencia_min', 'indice_referencia_max', 'actualizacion_renta',
  'situacion_5_anios', 'gran_tenedor', 'zona_tensionada', 'descripcion_es',
  'descripcion_en', 'descripcion_cat', 'usos',
  'gtos_comunidad', 'ibi_incluido', 'ibi', 'situacion_actual',
  'n_habitaciones', 'notas_web', 'matterport_URI',
]
# Owner and internal data: never serialized publicly.
INMUEBLE_PRIVATE_FIELDS = [
  'propietario', 'notas_internas', 'otros_datos', 'original_Id', 'cat_nrc',
  'valor_plz', 'renta_plz', 'publicar_web', 'fecha_baja', 'fecha_firma',
  'fecha_entrega', 'created_at', 'updated_at',
]
# Nested objects and computed values (declared on the serializer, not columns).
INMUEBLE_NESTED_FIELDS = [
  'n_banyos', 'modalidades', 'es_venta', 'images', 'provincia', 'municipio', 'distrito', 'barrio', 'condiciones',
  'otros', 'banios', 'dormitorios', 'instalaciones', 'arearecreo', 'dotacion',
  'cocina', 'terraza', 'salon', 'carpinteria', 'otros_espacios', 'seguridad',
  'entorno', 'transporte',
]

class SingleInmuebleSerializer(DerivedFieldsMixin, serializers.ModelSerializer):
  images = SingleImageSerializer(many=True, read_only=True)
  provincia = ProvinciasSerializer(read_only=True)
  municipio = MunicipiosSerializer(read_only=True)
  distrito = DistritosSerializer(read_only=True)
  barrio = BarriosSerializer(read_only=True)
  otros = OtrosSerializer(read_only=True)
  banios = BaniosSerializer(read_only=True)
  dormitorios = DormitoriosSerializer(read_only=True)
  instalaciones = InstalacionesSerializer(read_only=True)
  arearecreo = AreaRecreoSerializer(read_only=True)
  dotacion = DotacionSerializer(read_only=True)
  cocina = CocinaSerializer(read_only=True)
  terraza = TerrazaSerializer(read_only=True)
  salon = SalonSerializer(read_only=True)
  carpinteria = CarpinteriaSerializer(read_only=True)
  otros_espacios = OtrosEspaciosSerializer(source='otrosespacios', read_only=True)
  seguridad = SeguridadSerializer(read_only=True)
  entorno = EntornoSerializer(read_only=True)
  transporte = TransporteSerializer(read_only=True)
  condiciones = serializers.SerializerMethodField()

  def get_condiciones(self, obj):
    condiciones = obj.condiciones or CondicionesAlquiler.objects.filter(por_defecto=True).first()
    return CondicionesAlquilerSerializer(condiciones).data if condiciones else None

  class Meta:
    model = Inmueble
    # Allow-list: a new Inmueble column stays private until it is added here
    # (base.tests.PublicFieldsTests fails until every column is classified).
    fields = INMUEBLE_PUBLIC_FIELDS + INMUEBLE_NESTED_FIELDS
