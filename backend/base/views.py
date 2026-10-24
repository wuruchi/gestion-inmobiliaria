from typing import Tuple, Union
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ParseError
from rest_framework.throttling import AnonRateThrottle
from rest_framework import status
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .models import Inmueble, Barrio, Modalidad, Distrito, Municipio, Provincia
from .serializers import InmuebleSerializer, SingleInmuebleSerializer, SolicitudReservaSerializer, DistritosSerializer, MunicipiosSerializer, ProvinciasSerializer, MunicipiosListItemSerializer, DistritosListItemSerializer, BarriosSerializer, ModalidadSerializer


INMUEBLES_PER_PAGE = 5

# Everything InmuebleSerializer reads, fetched in 2 queries instead of ~15 per listing.
def inmuebles_publicados(**filters):
  return Inmueble.objects.filter(publicar_web=True, **filters).select_related(
    'provincia', 'municipio__provincia', 'distrito__municipio__provincia', 'barrio',
    'otros', 'banios', 'dormitorios', 'instalaciones', 'arearecreo', 'dotacion',
    'cocina', 'terraza',
  ).prefetch_related('images', 'modalidades').order_by('-estado', 'fecha_disponibilidad', '_id')

def parse_request(request, precio_field='importe_alquiler__lte'):
  fecha_entradata = request.query_params.get('fecha_entrada')
  provincia = request.query_params.get('provincia')
  municipio = request.query_params.get('municipio')
  distrito = request.query_params.get('distrito')
  barrio = request.query_params.get('barrio')
  referencia = request.query_params.get('referencia')
  try:
    habitaciones = int(request.query_params.get('habitaciones', 0))
    max_precio = float(request.query_params.get('max_precio', 0.0))
    provincia = int(provincia) if provincia else 0
    municipio = int(municipio) if municipio else 0
    distrito = int(distrito) if distrito else 0
    barrio = int(barrio) if barrio else 0
  except ValueError:
    raise ParseError('Invalid numeric query parameter')
  kwargs = {}
  if fecha_entradata is not None and len(fecha_entradata) > 0:
    kwargs['fecha_disponibilidad__lte'] = fecha_entradata
  if provincia > 0:
    kwargs['provincia'] = provincia
  if municipio > 0:
    kwargs['municipio'] = municipio
  if distrito > 0:
    kwargs['distrito'] = distrito
  if barrio > 0:
    kwargs['barrio'] = barrio
  if referencia is not None and len(referencia) > 0:
    kwargs['referencia__icontains'] = referencia
  if habitaciones > 0:
    kwargs['n_habitaciones'] = habitaciones
  if max_precio > 0:
    kwargs[precio_field] = max_precio
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
  inmuebles = inmuebles_publicados(**parse_request(request))
  inmuebles, paginator = paginator_handler(inmuebles, page)
  serializer = InmuebleSerializer(inmuebles, many=True, context={'request': request})
  return Response({'inmuebles' : serializer.data, 'page': page, 'pages': paginator.num_pages })

@api_view(['GET'])
def getInmueblesHabituales(request):
  page = request.query_params.get('page', 1)
  inmuebles = inmuebles_publicados(modalidades__codigo='habitual', **parse_request(request))
  inmuebles, paginator = paginator_handler(inmuebles, page)
  serializer = InmuebleSerializer(inmuebles, many=True, context={'request': request})
  return Response({'inmuebles' : serializer.data, 'page': page, 'pages': paginator.num_pages })


@api_view(['GET'])
def getInmueblesTemporales(request):
  page = request.query_params.get('page', 1)
  inmuebles = inmuebles_publicados(modalidades__codigo='temporal', **parse_request(request))
  inmuebles, paginator = paginator_handler(inmuebles, page)
  serializer = InmuebleSerializer(inmuebles, many=True, context={'request': request})
  return Response({'inmuebles' : serializer.data, 'page': page, 'pages': paginator.num_pages })

@api_view(['GET'])
def getInmueblesVenta(request):
  page = request.query_params.get('page', 1)  
  inmuebles = inmuebles_publicados(modalidades__codigo='venta', **parse_request(request, 'importe_venta__lte'))
  inmuebles, paginator = paginator_handler(inmuebles, page)
  serializer = InmuebleSerializer(inmuebles, many=True, context={'request': request})
  return Response({'inmuebles' : serializer.data, 'page': page, 'pages': paginator.num_pages })


@api_view(['GET'])
def getInmueble(request, pk):
  inmueble = get_object_or_404(
    Inmueble.objects.select_related(
      'provincia', 'municipio', 'distrito', 'barrio', 'condiciones', 'otros', 'banios',
      'dormitorios', 'instalaciones', 'arearecreo', 'dotacion', 'cocina',
      'terraza', 'salon', 'carpinteria', 'otrosespacios', 'seguridad',
      'entorno', 'transporte',
    ).prefetch_related('images', 'modalidades'),
    _id=pk, publicar_web=True)
  serializer = SingleInmuebleSerializer(inmueble, many=False, context={'request': request})
  return Response(serializer.data)

class SolicitudReservaThrottle(AnonRateThrottle):
  rate = '10/hour'

@api_view(['POST'])
@throttle_classes([SolicitudReservaThrottle])
def crearSolicitudReserva(request, pk):
  inmueble = get_object_or_404(Inmueble, _id=pk, publicar_web=True)
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
  distrito = get_object_or_404(Distrito, _id=distrito_id)
  codigo = MODALIDAD_POR_URL.get(modalidad)
  if codigo is None:
    raise ParseError('Modalidad invalida')
  count = Inmueble.objects.filter(distrito_id=distrito_id, modalidades__codigo=codigo, publicar_web=True).count()
  return Response({'distrito_id': distrito._id, 'distrito': distrito.nombre, 'modalidad': modalidad, 'count': count})
