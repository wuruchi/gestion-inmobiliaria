from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from .models import Condiciones, ImageInmueble, Inmueble, InmuebleModalidad, Municipio, RegulacionAlquiler
from .serializers import (
  AgenciaSerializer, CondicionesSerializer, InclusionesAlquilerSerializer, ModalidadSerializer,
  OcultarDireccionMixin, RegulacionAlquilerSerializer, SingleImageSerializer, SingleInmuebleSerializer,
  TerminosAlquilerSerializer,
)

MONEDA = 'EUR'


class MunicipioTarjetaSerializer(serializers.ModelSerializer):
  class Meta:
    model = Municipio
    fields = ['id', 'nombre', 'slug']


class InmuebleTarjetaSerializer(OcultarDireccionMixin, serializers.ModelSerializer):
  """The listing as shown inside an offer card: identity, place, headline numbers and the main photo."""
  municipio = MunicipioTarjetaSerializer(read_only=True)
  zona = serializers.SerializerMethodField()
  zona_ref = serializers.SerializerMethodField()
  n_banios = serializers.SerializerMethodField()
  imagen = serializers.SerializerMethodField()

  class Meta:
    model = Inmueble
    fields = ['id', 'referencia', 'titulo', 'tipo', 'subtipo', 'sup_construida', 'sup_util', 'n_habitaciones',
              'n_banios', 'dir_descripcion', 'zona', 'zona_ref', 'municipio', 'imagen']

  def get_zona(self, obj):
    lugar = obj.barrio or obj.distrito
    return lugar.nombre if lugar else None

  def get_zona_ref(self, obj):
    return obj.distrito.nombre if obj.distrito else None

  def get_n_banios(self, obj):
    try:
      return obj.distribucion.banios
    except ObjectDoesNotExist:
      return None

  def get_imagen(self, obj):
    # The default photo, else the first one; floor plans never. Uses the prefetched photos.
    fotos = [i for i in obj.images.all() if i.tipo != ImageInmueble.PLANO]
    if not fotos:
      return None
    foto = next((i for i in fotos if i.default), fotos[0])
    return SingleImageSerializer(foto, context=self.context).data


class OfertaResumenSerializer(serializers.ModelSerializer):
  """What every offer shows: kind, price, deposit, state and availability."""
  modalidad = ModalidadSerializer(read_only=True)
  precio = serializers.SerializerMethodField()
  fianza = serializers.SerializerMethodField()

  class Meta:
    model = InmuebleModalidad
    fields = ['id', 'modalidad', 'precio', 'fianza', 'estado', 'fecha_disponibilidad']

  def get_precio(self, obj):
    # Money is a decimal string; `importe` is the price as advertised (net when `mas_iva`).
    por_m2 = None
    superficie = obj.inmueble.sup_construida
    if superficie:
      por_m2 = str((Decimal(str(obj.precio)) / Decimal(str(superficie))).quantize(Decimal('0.01')))
    return {
      'importe': str(obj.precio),
      'moneda': MONEDA,
      'unidad': obj.modalidad.unidad_precio,
      'mas_iva': obj.mas_iva,
      'tipo_iva': None if obj.tipo_iva is None else str(obj.tipo_iva),
      'por_m2': por_m2,
    }

  def get_fianza(self, obj):
    if obj.fianza_meses is None:
      return None
    return {'meses': obj.fianza_meses, 'importe': str(obj.fianza_total), 'moneda': MONEDA}


class OfertaTarjetaSerializer(OfertaResumenSerializer):
  inmueble = InmuebleTarjetaSerializer(read_only=True)

  class Meta(OfertaResumenSerializer.Meta):
    fields = OfertaResumenSerializer.Meta.fields + ['inmueble']


class OfertaDetalleSerializer(OfertaResumenSerializer):
  # Rent regulation: null for a sale; a rental without a record is "desconocida".
  regulacion = serializers.SerializerMethodField()
  # Stay limits and pets of a rental: null for a sale or when nothing was recorded.
  terminos = serializers.SerializerMethodField()
  # What the rent includes: null for a sale or when nothing was recorded.
  inclusiones = serializers.SerializerMethodField()
  # The offer's own conditions, else the modalidad's default.
  condiciones = serializers.SerializerMethodField()
  inmueble = SingleInmuebleSerializer(read_only=True)
  otras_ofertas = serializers.SerializerMethodField()
  agencia = AgenciaSerializer(source='inmueble.agencia', read_only=True)

  class Meta(OfertaResumenSerializer.Meta):
    fields = OfertaResumenSerializer.Meta.fields + [
      'regulacion', 'terminos', 'inclusiones', 'condiciones', 'inmueble', 'otras_ofertas', 'agencia']

  def get_regulacion(self, obj):
    if obj.modalidad.unidad_precio != 'mensual':
      return None
    try:
      return RegulacionAlquilerSerializer(obj.regulacion).data
    except ObjectDoesNotExist:
      return RegulacionAlquilerSerializer(RegulacionAlquiler()).data

  def get_terminos(self, obj):
    try:
      return TerminosAlquilerSerializer(obj.terminos).data
    except ObjectDoesNotExist:
      return None

  def get_inclusiones(self, obj):
    try:
      return InclusionesAlquilerSerializer(obj.inclusiones).data
    except ObjectDoesNotExist:
      return None

  def get_condiciones(self, obj):
    if obj.condiciones_id:
      condiciones = obj.condiciones
    else:
      if 'condiciones_por_defecto' not in self.context:
        self.context['condiciones_por_defecto'] = {
          c.modalidad_id: c for c in Condiciones.objects.filter(por_defecto=True)
        }
      condiciones = self.context['condiciones_por_defecto'].get(obj.modalidad_id)
    return CondicionesSerializer(condiciones).data if condiciones else None

  def get_otras_ofertas(self, obj):
    otras = [o for o in obj.inmueble.precios.all() if o.pk != obj.pk]
    return OfertaResumenSerializer(otras, many=True, context=self.context).data
