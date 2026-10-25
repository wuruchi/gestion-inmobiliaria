import math
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db.models import Case, Exists, F, IntegerField, OuterRef, Q, Value, When
from rest_framework.exceptions import ValidationError
from .models import Inmueble, InmuebleModalidad, Modalidad, PlazaAparcamiento

ESTADOS_POR_DEFECTO = [InmuebleModalidad.DISPONIBLE, InmuebleModalidad.RESERVADO]

# Feature filter -> condition on the offer. Only `true` is accepted: a missing row is unknown, not "no".
CARACTERISTICAS = {
  'amueblado': Q(inmueble__dotacion__amueblado=True),
  'animales': Q(terminos__acepta_animales=True),
  'piscina': Q(inmueble__arearecreo__piscina=True),
  'ascensor': Q(inmueble__instalaciones__ascensor__gt=0),
  'terraza': Q(inmueble__estancias__n_terrazas__gt=0),
}

ORDENES = {
  'precio': ('precio', 'id'),
  '-precio': ('-precio', 'id'),
  '-fecha_alta': ('-inmueble__fecha_alta', 'id'),
  'sup': (F('inmueble__sup_construida').asc(nulls_last=True), 'id'),
}


class Parametros:
  """Reads the query string of an offer search; every problem is collected and raised together, by field."""

  def __init__(self, params):
    self.params = params
    self.errores = {}

  def error(self, nombre, mensaje):
    self.errores.setdefault(nombre, []).append(mensaje)

  def texto(self, nombre):
    return self.params.get(nombre) or None

  def decimal(self, nombre):
    valor = self.texto(nombre)
    if valor is None:
      return None
    try:
      numero = Decimal(valor)
    except InvalidOperation:
      numero = None
    if numero is None or not numero.is_finite() or numero < 0:
      self.error(nombre, 'Debe ser un número no negativo.')
      return None
    return numero

  def entero(self, nombre):
    valor = self.texto(nombre)
    if valor is None:
      return None
    if not valor.isdigit():
      self.error(nombre, 'Debe ser un entero no negativo.')
      return None
    return int(valor)

  def fecha(self, nombre):
    valor = self.texto(nombre)
    if valor is None:
      return None
    try:
      return date.fromisoformat(valor)
    except ValueError:
      self.error(nombre, 'Debe ser una fecha AAAA-MM-DD.')
      return None

  def eleccion(self, nombre, validas):
    valor = self.texto(nombre)
    if valor is not None and valor not in validas:
      self.error(nombre, f'Valor no válido: {valor}.')
      return None
    return valor

  def verdadero(self, nombre):
    valor = self.texto(nombre)
    if valor is None:
      return False
    if valor.lower() not in ('true', '1'):
      self.error(nombre, 'Solo se admite true: un dato ausente es desconocido, no "no".')
      return False
    return True

  def estados(self):
    valor = self.texto('estado')
    if valor is None:
      return ESTADOS_POR_DEFECTO
    lista = [e.strip() for e in valor.split(',') if e.strip()]
    validos = dict(InmuebleModalidad.ESTADOS)
    if not lista or any(e not in validos for e in lista):
      self.error('estado', f'Use uno o varios de: {", ".join(validos)}.')
      return ESTADOS_POR_DEFECTO
    return lista


def _lugar(q, nombre, valor):
  """A location by id (digits) or by slug. A slug is unique only inside its parent, so it may match several."""
  clave = 'id' if valor.isdigit() else 'slug'
  return q & Q(**{f'inmueble__{nombre}__{clave}': valor})


def ofertas_publicadas():
  """Offers of published listings, with everything the card needs in a fixed number of queries."""
  return (
    InmuebleModalidad.objects.filter(inmueble__publicar_web=True)
    .select_related('modalidad', 'inmueble__municipio', 'inmueble__distrito', 'inmueble__barrio', 'inmueble__distribucion')
    .prefetch_related('inmueble__images')
  )


def filtrar_ofertas(queryset, params):
  """Apply the search filters and the `sort` of `GET /ofertas`; a bad value is a 400 naming the field."""
  p = Parametros(params)
  q = Q()

  codigo = p.texto('modalidad')
  if codigo and not Modalidad.objects.filter(codigo=codigo).exists():
    p.error('modalidad', f'Modalidad desconocida: {codigo}.')
  elif codigo:
    q &= Q(modalidad__codigo=codigo)
  q &= Q(estado__in=p.estados())

  for nombre in ('municipio', 'distrito', 'barrio'):
    valor = p.texto(nombre)
    if valor:
      q = _lugar(q, nombre, valor)

  tipo = p.eleccion('tipo', dict(Inmueble.TIPOS))
  subtipo = p.eleccion('subtipo', dict(Inmueble.SUBTIPOS))
  if tipo:
    q &= Q(inmueble__tipo=tipo)
  if subtipo:
    q &= Q(inmueble__subtipo=subtipo)

  # The price is the offer's own, as advertised. Without `modalidad`, rents and sales share one scale: pass it.
  limites = [
    ('precio_min', 'precio__gte'), ('precio_max', 'precio__lte'),
    ('sup_min', 'inmueble__sup_construida__gte'), ('sup_max', 'inmueble__sup_construida__lte'),
  ]
  for nombre, lookup in limites:
    valor = p.decimal(nombre)
    if valor is not None:
      q &= Q(**{lookup: valor})

  banios = p.entero('banios_min')
  if banios is not None:
    q &= Q(inmueble__distribucion__banios__gte=banios)
  habitaciones = p.entero('habitaciones_min')
  if habitaciones is not None:
    # Same sum as `Inmueble.n_habitaciones`; a listing with unknown rooms never matches.
    con_habitaciones = Inmueble.objects.con_habitaciones().filter(habitaciones_total__gte=habitaciones)
    q &= Q(inmueble__in=con_habitaciones.values('pk'))

  antes = p.fecha('disponible_antes')
  if antes is not None:
    q &= Q(fecha_disponibilidad__lte=antes)

  for nombre, condicion in CARACTERISTICAS.items():
    if p.verdadero(nombre):
      q &= condicion
  if p.verdadero('parking'):
    plazas = PlazaAparcamiento.objects.filter(inmueble=OuterRef('inmueble_id'))
    q &= Q(Exists(plazas)) | Q(inmueble__tipo='parking')

  orden = p.texto('sort')
  if orden is not None and orden not in ORDENES:
    p.error('sort', f'Use uno de: {", ".join(ORDENES)}.')

  if p.errores:
    raise ValidationError(p.errores)

  if orden:
    ordenado = queryset.order_by(*ORDENES[orden])
  else:
    # Available first, then reserved, then closed; soonest availability first.
    rango = Case(
      When(estado=InmuebleModalidad.DISPONIBLE, then=Value(0)),
      When(estado=InmuebleModalidad.RESERVADO, then=Value(1)),
      default=Value(2), output_field=IntegerField(),
    )
    ordenado = queryset.annotate(orden_estado=rango).order_by('orden_estado', 'fecha_disponibilidad', 'id')
  return ordenado.filter(q)


def parsear_bbox(valor):
  """`bbox=minLon,minLat,maxLon,maxLat` (RFC 7946 order) as four floats; a 400 on `bbox` if it is not valid."""
  try:
    min_lon, min_lat, max_lon, max_lat = (float(v) for v in valor.split(','))
  except ValueError:
    min_lon = None
  if min_lon is None or not all(math.isfinite(v) for v in (min_lon, min_lat, max_lon, max_lat)) \
      or not (-180 <= min_lon < max_lon <= 180 and -90 <= min_lat < max_lat <= 90):
    raise ValidationError({'bbox': ['Use minLon,minLat,maxLon,maxLat, con mínimos menores que máximos.']})
  return min_lon, min_lat, max_lon, max_lat
