from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from .filtros_ofertas import filtrar_ofertas, ofertas_publicadas, parsear_bbox
from django.http import Http404
from django.utils.cache import patch_vary_headers
from django.views.decorators.cache import cache_control
from .models import Agencia, Barrio, Distrito, Inmueble, InmuebleModalidad, Modalidad, Municipio, Provincia
from .paginacion import PaginacionOfertas, PaginacionReferencias
from .serializers import AgenciaSerializer, BarriosSerializer, DistritosListItemSerializer, ModalidadSerializer, MunicipiosListItemSerializer, ProvinciasSerializer, SolicitudReservaSerializer
from .serializers import PASO_COORDENADAS_OCULTAS, difuminar
from .serializers_ofertas import OfertaDetalleSerializer, OfertaTarjetaSerializer


@api_view(['GET'])
def listarOfertas(request):
  ofertas = filtrar_ofertas(ofertas_publicadas(), request.query_params)
  paginador = PaginacionOfertas()
  pagina = paginador.paginate_queryset(ofertas, request)
  serializer = OfertaTarjetaSerializer(pagina, many=True, context={'request': request})
  return paginador.get_paginated_response(serializer.data)

MAPA_MAXIMO = 1000

@api_view(['GET'])
def mapaOfertas(request):
  """The offers that pass the search filters as GeoJSON points (RFC 7946), at most `MAPA_MAXIMO`.

  A hidden address is placed at the snapped point, and `bbox` is checked against the point the client would see:
  filtering on the exact one would let a client narrow a box until it found the real position.
  """
  bbox = request.query_params.get('bbox')
  limites = parsear_bbox(bbox) if bbox else None
  ofertas = InmuebleModalidad.objects.filter(
    inmueble__publicar_web=True, inmueble__geo_latitude__isnull=False, inmueble__geo_longitude__isnull=False,
  ).select_related('modalidad', 'inmueble')
  if limites:
    margen = PASO_COORDENADAS_OCULTAS  # the snapped point can be this far from the real one
    ofertas = ofertas.filter(
      inmueble__geo_longitude__gte=limites[0] - margen, inmueble__geo_longitude__lte=limites[2] + margen,
      inmueble__geo_latitude__gte=limites[1] - margen, inmueble__geo_latitude__lte=limites[3] + margen)
  caracteristicas, truncado = [], False
  for oferta in filtrar_ofertas(ofertas, request.query_params).iterator():
    inmueble = oferta.inmueble
    lon, lat = inmueble.geo_longitude, inmueble.geo_latitude
    if inmueble.ocultar_direccion:
      lon, lat = difuminar(lon), difuminar(lat)
    if limites and not (limites[0] <= lon <= limites[2] and limites[1] <= lat <= limites[3]):
      continue
    if len(caracteristicas) == MAPA_MAXIMO:
      truncado = True
      break
    caracteristicas.append({
      'type': 'Feature',
      'id': str(oferta.pk),
      'geometry': {'type': 'Point', 'coordinates': [lon, lat]},
      'properties': {
        'modalidad': oferta.modalidad.codigo, 'tipo': inmueble.tipo, 'estado': oferta.estado,
        'precio': str(oferta.precio), 'moneda': 'EUR', 'unidad': oferta.modalidad.unidad_precio,
      },
    })
  return Response({'type': 'FeatureCollection', 'features': caracteristicas, 'truncated': truncado},
                  content_type='application/geo+json')

@api_view(['GET'])
def getOferta(request, pk):
  # A closed offer (rented, sold) stays reachable; only an unpublished listing is hidden.
  oferta = get_object_or_404(
    InmuebleModalidad.objects.filter(inmueble__publicar_web=True).select_related(
      'modalidad', 'condiciones', 'regulacion', 'terminos', 'inclusiones', 'inmueble__agencia',
      'inmueble__municipio__provincia', 'inmueble__distrito', 'inmueble__barrio', 'inmueble__caracteristicas',
      'inmueble__distribucion', 'inmueble__instalaciones', 'inmueble__arearecreo', 'inmueble__dotacion',
      'inmueble__estancias', 'inmueble__otrosespacios', 'inmueble__seguridad', 'inmueble__entorno',
      'inmueble__certificado_energetico',
    ).prefetch_related(
      'inmueble__images', 'inmueble__descripciones', 'inmueble__suministros', 'inmueble__transportes',
      'inmueble__plazas', 'inmueble__registros_legales', 'inmueble__medios', 'inmueble__propietarios',
      'inmueble__municipio__declaraciones_tensionada',
      Prefetch('inmueble__precios', queryset=InmuebleModalidad.objects.select_related('modalidad')),
    ),
    pk=pk)
  respuesta = Response(OfertaDetalleSerializer(oferta, context={'request': request}).data)
  patch_vary_headers(respuesta, ['Accept-Language'])  # `inmueble.descripcion` depends on it
  return respuesta

class SolicitudReservaThrottle(AnonRateThrottle):
  rate = '10/hour'

@api_view(['POST'])
@throttle_classes([SolicitudReservaThrottle])
def crearSolicitud(request, pk):
  oferta = get_object_or_404(InmuebleModalidad.objects.select_related('inmueble'), pk=pk, inmueble__publicar_web=True)
  serializer = SolicitudReservaSerializer(data=request.data)
  serializer.is_valid(raise_exception=True)
  solicitud = serializer.save(inmueble=oferta.inmueble)
  # The request cannot be read back by the public (it holds personal data); the URL only identifies it.
  ubicacion = request.build_absolute_uri(f'{request.path.rstrip("/")}/{solicitud.pk}')
  return Response(serializer.data, status=status.HTTP_201_CREATED, headers={'Location': ubicacion})

# Reference data changes rarely: browsers and proxies may keep it for an hour.
referencia_cacheable = cache_control(public=True, max_age=3600)

def _por_id_o_slug(queryset, campo, valor):
  """Filter by the id (digits) or the slug of a parent place."""
  return queryset.filter(**{f'{campo}__{"id" if valor.isdigit() else "slug"}': valor})

def _lista_paginada(request, queryset, serializer):
  paginador = PaginacionReferencias()
  pagina = paginador.paginate_queryset(queryset, request)
  return paginador.get_paginated_response(serializer(pagina, many=True).data)

@api_view(['GET'])
@referencia_cacheable
def listarProvincias(request):
  return Response(ProvinciasSerializer(Provincia.objects.all(), many=True).data)

@api_view(['GET'])
@referencia_cacheable
def listarMunicipios(request):
  municipios = Municipio.objects.all()
  if request.query_params.get('provincia'):
    municipios = _por_id_o_slug(municipios, 'provincia', request.query_params['provincia'])
  if request.query_params.get('q'):
    municipios = municipios.filter(nombre__icontains=request.query_params['q'])
  return _lista_paginada(request, municipios, MunicipiosListItemSerializer)

@api_view(['GET'])
@referencia_cacheable
def listarDistritos(request):
  distritos = Distrito.objects.all()
  if request.query_params.get('municipio'):
    distritos = _por_id_o_slug(distritos, 'municipio', request.query_params['municipio'])
  return _lista_paginada(request, distritos, DistritosListItemSerializer)

@api_view(['GET'])
@referencia_cacheable
def listarBarrios(request):
  barrios = Barrio.objects.all()
  if request.query_params.get('distrito'):
    barrios = _por_id_o_slug(barrios, 'distrito', request.query_params['distrito'])
  return _lista_paginada(request, barrios, BarriosSerializer)

def _opciones(choices):
  return [{'codigo': codigo, 'nombre': str(nombre)} for codigo, nombre in choices]

@api_view(['GET'])
@referencia_cacheable
def getCatalogos(request):
  """The closed lists a search form needs: types, subtypes, conservation, offer states and modalidades."""
  return Response({
    'tipos': _opciones(Inmueble.TIPOS),
    'subtipos': _opciones(Inmueble.SUBTIPOS),
    'conservaciones': _opciones(Inmueble.CONSERVACIONES),
    'estados': _opciones(InmuebleModalidad.ESTADOS),
    'modalidades': ModalidadSerializer(Modalidad.objects.all(), many=True).data,
  })

@api_view(['GET'])
@referencia_cacheable
def getAgencia(request):
  """The agency that runs the site: the first one created (the seed loads it first)."""
  agencia = Agencia.objects.order_by('pk').first()
  if agencia is None:
    raise Http404
  return Response(AgenciaSerializer(agencia).data)
