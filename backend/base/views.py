from datetime import date
from typing import Tuple, Union
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ParseError
from rest_framework.throttling import AnonRateThrottle
from rest_framework import status
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import F, Prefetch, Q
from .models import Inmueble, InmuebleModalidad, Barrio, Modalidad, Distrito, Municipio, Provincia
from .serializers import InmuebleSerializer, SingleInmuebleSerializer, SolicitudReservaSerializer, DistritosSerializer, MunicipiosSerializer, ProvinciasSerializer, MunicipiosListItemSerializer, DistritosListItemSerializer, BarriosSerializer, ModalidadSerializer


INMUEBLES_PER_PAGE = 5

# Everything InmuebleSerializer reads, fetched in 2 queries instead of ~15 per listing.
def inmuebles_publicados(**filters):
  return Inmueble.objects.con_habitaciones().con_orden_estado().con_disponibilidad().filter(publicar_web=True, **filters).select_related(
    'municipio__provincia', 'distrito__municipio__provincia', 'barrio',
    'caracteristicas', 'distribucion', 'instalaciones', 'arearecreo', 'dotacion',
    'estancias',
  ).prefetch_related(
    'images', 'descripciones', 'suministros',
    Prefetch('precios', queryset=InmuebleModalidad.objects.select_related('modalidad')),
  ).order_by('orden_estado', F('proxima_disponibilidad').asc(nulls_last=True), 'id')

def parse_request(request, modalidad=None):
  fecha_entradata = request.query_params.get('fecha_entrada')
  provincia = request.query_params.get('provincia')
  municipio = request.query_params.get('municipio')
  distrito = request.query_params.get('distrito')
  barrio = request.query_params.get('barrio')
  referencia = request.query_params.get('referencia')
  tipo = request.query_params.get('tipo')
  subtipo = request.query_params.get('subtipo')
  if tipo and tipo not in dict(Inmueble.TIPOS):
    raise ParseError('Invalid tipo')
  if subtipo and subtipo not in dict(Inmueble.SUBTIPOS):
    raise ParseError('Invalid subtipo')
  try:
    sup_min = float(request.query_params.get('sup_min', 0.0))
    sup_max = float(request.query_params.get('sup_max', 0.0))
    habitaciones = int(request.query_params.get('habitaciones', 0))
    max_precio = float(request.query_params.get('max_precio', 0.0))
    provincia = int(provincia) if provincia else 0
    municipio = int(municipio) if municipio else 0
    distrito = int(distrito) if distrito else 0
    barrio = int(barrio) if barrio else 0
  except ValueError:
    raise ParseError('Invalid numeric query parameter')
  kwargs = {}
  if fecha_entradata:
    try:
      fecha_entrada = date.fromisoformat(fecha_entradata)
    except ValueError:
      raise ParseError('Invalid fecha_entrada')
    # One offer must be open and available by then; with a modalidad or a price it is that same offer.
    kwargs['precios__fecha_disponibilidad__lte'] = fecha_entrada
    kwargs['precios__estado__in'] = [InmuebleModalidad.DISPONIBLE, InmuebleModalidad.RESERVADO]
  if provincia > 0:
    kwargs['municipio__provincia'] = provincia
  if municipio > 0:
    kwargs['municipio'] = municipio
  if distrito > 0:
    kwargs['distrito'] = distrito
  if barrio > 0:
    kwargs['barrio'] = barrio
  if tipo:
    kwargs['tipo'] = tipo
  if subtipo:
    kwargs['subtipo'] = subtipo
  # Built surface in m².
  if sup_min > 0:
    kwargs['sup_construida__gte'] = sup_min
  if sup_max > 0:
    kwargs['sup_construida__lte'] = sup_max
  if referencia is not None and len(referencia) > 0:
    kwargs['referencia__icontains'] = referencia
  if habitaciones > 0:
    kwargs['habitaciones_total'] = habitaciones
  if modalidad:
    kwargs['precios__modalidad__codigo'] = modalidad
  if max_precio > 0:
    # Same join as the modalidad above, so the price is that modalidad's price.
    # Without a modalidad, compare the monthly prices (rent).
    if not modalidad:
      kwargs['precios__modalidad__unidad_precio'] = 'mensual'
    kwargs['precios__precio__lte'] = max_precio
  return kwargs

def paginator_handler(inmuebles, page):
  paginator = Paginator(inmuebles, INMUEBLES_PER_PAGE)
  try:
    inmuebles = paginator.page(page)
  except PageNotAnInteger:
    inmuebles = paginator.page(1)
  except EmptyPage:
    inmuebles = paginator.page(paginator.num_pages)
  return inmuebles, paginator

# Create your views here.
@api_view(['GET'])
def getRoutes(request):
  return Response('Hello')

@api_view(['GET'])
def getInmuebles(request):
  page = request.query_params.get('page', 1)
  inmuebles = inmuebles_publicados(**parse_request(request)).distinct()
  inmuebles, paginator = paginator_handler(inmuebles, page)
  serializer = InmuebleSerializer(inmuebles, many=True, context={'request': request})
  return Response({'inmuebles' : serializer.data, 'page': page, 'pages': paginator.num_pages })

@api_view(['GET'])
def getInmueblesHabituales(request):
  page = request.query_params.get('page', 1)
  inmuebles = inmuebles_publicados(**parse_request(request, 'habitual'))
  inmuebles, paginator = paginator_handler(inmuebles, page)
  serializer = InmuebleSerializer(inmuebles, many=True, context={'request': request})
  return Response({'inmuebles' : serializer.data, 'page': page, 'pages': paginator.num_pages })


@api_view(['GET'])
def getInmueblesTemporales(request):
  page = request.query_params.get('page', 1)
  inmuebles = inmuebles_publicados(**parse_request(request, 'temporal'))
  inmuebles, paginator = paginator_handler(inmuebles, page)
  serializer = InmuebleSerializer(inmuebles, many=True, context={'request': request})
  return Response({'inmuebles' : serializer.data, 'page': page, 'pages': paginator.num_pages })

@api_view(['GET'])
def getInmueblesVenta(request):
  page = request.query_params.get('page', 1)  
  inmuebles = inmuebles_publicados(**parse_request(request, 'venta'))
  inmuebles, paginator = paginator_handler(inmuebles, page)
  serializer = InmuebleSerializer(inmuebles, many=True, context={'request': request})
  return Response({'inmuebles' : serializer.data, 'page': page, 'pages': paginator.num_pages })


@api_view(['GET'])
def getInmueble(request, pk):
  inmueble = get_object_or_404(
    Inmueble.objects.select_related(
      'municipio__provincia', 'distrito', 'barrio', 'caracteristicas', 'distribucion',
      'instalaciones', 'arearecreo', 'dotacion', 'estancias',
      'otrosespacios', 'seguridad',
      'entorno', 'certificado_energetico', 'agencia',
    ).prefetch_related(
      'images', 'descripciones', 'suministros', 'transportes', 'plazas', 'registros_legales', 'medios', 'propietarios',
      'municipio__declaraciones_tensionada',
      Prefetch('precios', queryset=InmuebleModalidad.objects.select_related('modalidad', 'condiciones', 'regulacion', 'terminos', 'inclusiones')),
    ),
    id=pk, publicar_web=True)
  serializer = SingleInmuebleSerializer(inmueble, many=False, context={'request': request})
  return Response(serializer.data)

class SolicitudReservaThrottle(AnonRateThrottle):
  rate = '10/hour'

@api_view(['POST'])
@throttle_classes([SolicitudReservaThrottle])
def crearSolicitudReserva(request, pk):
  inmueble = get_object_or_404(Inmueble, id=pk, publicar_web=True)
  serializer = SolicitudReservaSerializer(data=request.data)
  serializer.is_valid(raise_exception=True)
  serializer.save(inmueble=inmueble)
  return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def getDistritos(request):
  distritos = Distrito.objects
  serializer = DistritosSerializer(distritos, many=True)
  return Response(serializer.data)

@api_view(['GET'])
def getDistritosByMunicipio(request, municipio_id):
  distritos = Distrito.objects.filter(municipio_id=municipio_id)
  serializer = DistritosListItemSerializer(distritos, many=True)
  return Response(serializer.data)

@api_view(['GET'])
def getBarriosByDistrito(request, distrito_id):
  barrios = Barrio.objects.filter(distrito_id=distrito_id)
  serializer = BarriosSerializer(barrios, many=True)
  return Response(serializer.data)

@api_view(['GET'])
def getMunicipios(request):
  municipios = Municipio.objects
  serializer = MunicipiosSerializer(municipios, many=True)
  return Response(serializer.data)

@api_view(['GET'])
def getMunicipiosByProvincia(request, provincia_id):
  municipios = Municipio.objects.filter(provincia_id=provincia_id)
  serializer = MunicipiosListItemSerializer(municipios, many=True)
  return Response(serializer.data)

@api_view(['GET'])
def getProvincias(request):
  provincias = Provincia.objects
  serializer = ProvinciasSerializer(provincias, many=True)
  return Response(serializer.data)

# URL segment -> Modalidad.codigo
MODALIDAD_POR_URL = {'ventas': 'venta', 'habituales': 'habitual', 'temporales': 'temporal'}

@api_view(['GET'])
def getModalidades(request):
  return Response(ModalidadSerializer(Modalidad.objects.all(), many=True).data)

@api_view(['GET'])
def getInmueblesCount(request, modalidad, distrito_id):
  distrito = get_object_or_404(Distrito, id=distrito_id)
  codigo = MODALIDAD_POR_URL.get(modalidad)
  if codigo is None:
    raise ParseError('Modalidad invalida')
  count = Inmueble.objects.filter(distrito_id=distrito_id, modalidades__codigo=codigo, publicar_web=True).count()
  return Response({'distrito_id': distrito.id, 'distrito': distrito.nombre, 'modalidad': modalidad, 'count': count})
