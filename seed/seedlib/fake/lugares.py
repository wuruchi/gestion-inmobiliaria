"""Where a fake offer is: resolves the municipio and draws an address, barrio, postal code and coordinates.

Barcelona has real districts, barrios and streets (`data/fake/calles_barcelona.json`). Any other municipio gets
generic Catalan street names around its centre; if the database holds districts for it, one is drawn too.
"""
import json
import unicodedata

from ..fetch import DATA_DIR

BARCELONA_INE = '08019'
# Share of the offers of each Barcelona district (order of magnitude of the supply, not exact figures).
PESO_DISTRITO = {'01': 9, '02': 22, '03': 10, '04': 7, '05': 10, '06': 9, '07': 6, '08': 3, '09': 4, '10': 12}
DIR_FAKE = DATA_DIR / 'fake'


def _cargar(nombre):
    return json.loads((DIR_FAKE / nombre).read_text(encoding='utf-8'))


def normalizar(texto):
    sin_tildes = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode()
    return ' '.join(sin_tildes.lower().replace("'", ' ').replace('-', ' ').split())


def resolver_municipio(valor):
    """A municipio by 5-digit INE code or by name (any case, with or without accents)."""
    from base.models import Municipio

    valor = valor.strip()
    if valor.isdigit():
        encontrados = list(Municipio.objects.filter(codigo_ine=valor.zfill(5)))
    else:
        clave = normalizar(valor)
        encontrados = [m for m in Municipio.objects.all() if normalizar(m.nombre) == clave]
    if not encontrados:
        raise SystemExit(f'Municipio "{valor}" not found; load the locations first (python seed.py locations).')
    if len(encontrados) > 1:
        raise SystemExit('Several municipios match "%s": %s. Use the INE code.' % (
            valor, ', '.join(f'{m.nombre} ({m.codigo_ine})' for m in encontrados)))
    return encontrados[0]


class Lugares:
    """Draws places inside one municipio."""

    def __init__(self, municipio):
        from base.models import Barrio, Distrito

        self.municipio = municipio
        self.es_barcelona = municipio.codigo_ine == BARCELONA_INE
        self.distritos = list(Distrito.objects.filter(municipio=municipio))
        self.barrios = list(Barrio.objects.filter(distrito__municipio=municipio).select_related('distrito'))
        self.calles_bcn = _cargar('calles_barcelona.json') if self.es_barcelona else None
        self.genericas = _cargar('calles_genericas.json')['calles']
        precios = _cargar('precios.json')
        self.precios = precios
        self.datos_municipio = next(
            (datos for nombre, datos in precios['municipios'].items()
             if normalizar(nombre) == normalizar(municipio.nombre)), None)
        if self.es_barcelona and not self.barrios:
            raise SystemExit('Barcelona has no barrios loaded; run `python seed.py locations` first.')

    def distritos_codigos(self):
        return sorted({b.distrito.codigo for b in self.barrios})

    def elegir(self, rng, solo_distritos=None):
        """Returns a dict: distrito, barrio, zona, calle, numero, codigo_postal, lat, lon, distrito_codigo."""
        if self.es_barcelona:
            barrios = [b for b in self.barrios
                       if b.codigo in self.calles_bcn['barrios']
                       and (not solo_distritos or b.distrito.codigo in solo_distritos)]
            # First a district by how much of the market it holds, then one of its barrios.
            codigos = sorted({b.distrito.codigo for b in barrios})
            distrito_codigo = rng.choices(codigos, [PESO_DISTRITO.get(c, 5) for c in codigos])[0]
            barrio = rng.choice([b for b in barrios if b.distrito.codigo == distrito_codigo])
            datos = self.calles_bcn['barrios'][barrio.codigo]
            calle, desde, hasta = rng.choice(datos['calles'])
            return {
                'distrito': barrio.distrito, 'barrio': barrio, 'zona': barrio.nombre, 'calle': calle,
                'numero': rng.randint(desde, hasta), 'codigo_postal': rng.choice(datos['cp']),
                'lat': round(datos['lat'] + rng.uniform(-0.0025, 0.0025), 6),
                'lon': round(datos['lon'] + rng.uniform(-0.0035, 0.0035), 6),
                'distrito_codigo': barrio.distrito.codigo,
            }
        distrito = barrio = None
        zona = self.municipio.nombre
        if self.barrios:
            barrio = rng.choice(self.barrios)
            distrito = barrio.distrito
            zona = barrio.nombre
        lat, lon = self.municipio.latitud, self.municipio.longitud
        if self.datos_municipio and self.datos_municipio.get('cp'):
            cp = rng.choice(self.datos_municipio['cp'])
        else:
            cp = f'{self.municipio.codigo_ine[:2]}{rng.randint(1, 999):03d}'
        return {
            'distrito': distrito, 'barrio': barrio, 'zona': zona, 'calle': rng.choice(self.genericas),
            'numero': rng.randint(1, 90), 'codigo_postal': cp,
            'lat': None if lat is None else round(lat + rng.uniform(-0.01, 0.01), 6),
            'lon': None if lon is None else round(lon + rng.uniform(-0.012, 0.012), 6),
            'distrito_codigo': None,
        }

    def transporte(self, rng, distrito_codigo):
        """Rows `(tipo, descripcion)` of the public transport near the listing."""
        filas = []
        if self.es_barcelona and distrito_codigo:
            if rng.random() < 0.9:
                filas.append(('metro', rng.choice(self.calles_bcn['metro'][distrito_codigo])))
            if rng.random() < 0.9:
                filas.append(('bus', rng.choice(self.calles_bcn['bus'][distrito_codigo])))
            if distrito_codigo in ('03', '09', '10') and rng.random() < 0.3:
                filas.append(('tren', 'Rodalies R1, R2 i R3'))
            if distrito_codigo in ('04', '10') and rng.random() < 0.25:
                filas.append(('tranvia', 'T1, T2 i T3' if distrito_codigo == '04' else 'T4'))
        else:
            if rng.random() < 0.85:
                filas.append(('bus', 'Línies urbanes i interurbanes'))
            if rng.random() < 0.4:
                filas.append(('tren', 'Estació de Rodalies'))
        return filas

    def metros_a_playa(self, rng, distrito_codigo):
        if not self.es_barcelona or not distrito_codigo:
            return None
        rangos = {'01': (300, 1200), '10': (400, 2500), '03': (1800, 3500)}
        desde, hasta = rangos.get(distrito_codigo, (2000, 6500))
        return rng.randrange(desde, hasta, 50)
