"""Download the official location data and write it to data/*.json (stdlib only)."""
import csv
import io
import json
import re
import urllib.request
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'

PROVINCIA = {'codigo_ine': '08', 'nombre': 'Barcelona'}

SRC_MUNICIPIOS = (
    'https://analisi.transparenciacatalunya.cat/resource/9aju-tpwc.json'
    '?$limit=2000&$select=codi,nom,codi_comarca,nom_comarca,latitud,longitud'
)
SRC_IDESCAT = 'https://api.idescat.cat/emex/v1/nodes.json?tipus=mun&lang=ca'
SRC_BCN_DISTRITOS = (
    'https://opendata-ajuntament.barcelona.cat/data/dataset/'
    '808daafa-d9ce-48c0-925a-fa5afdb1ed41/resource/'
    '576bc645-9481-4bc4-b8bf-f5972c20df3f/download'
)
SRC_BCN_BARRIOS = (
    'https://opendata-ajuntament.barcelona.cat/data/dataset/'
    '808daafa-d9ce-48c0-925a-fa5afdb1ed41/resource/'
    'b21fa550-56ea-4f4c-9adc-b8009381896e/download'
)
BARCELONA_INE = '08019'
EXPECTED_BARRIOS_BCN = 73
EXPECTED_MUNICIPIOS = 311


def _get(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read().decode('utf-8-sig')


def fix_article(name):
    """'Hospitalet de Llobregat, l'' -> 'l'Hospitalet de Llobregat'."""
    match = re.match(r"^(.*), (l'|el|la|els|les)$", name)
    if not match:
        return name
    base, article = match.groups()
    return f'{article}{base}' if article.endswith("'") else f'{article} {base}'


def _write(name, sources, items):
    payload = {
        'sources': sources,
        'retrieved': date.today().isoformat(),
        'items': items,
    }
    path = DATA_DIR / f'{name}.json'
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'wrote {path.name}: {len(items)} items')


def fetch_locations():
    rows = [
        r for r in json.loads(_get(SRC_MUNICIPIOS))
        if r['codi'].startswith(PROVINCIA['codigo_ine'])
    ]
    # Cross-check against Idescat: the two sources must list the same municipalities.
    idescat = {
        m['id'] for m in json.loads(_get(SRC_IDESCAT))['fitxes']['v']
        if m['id'].startswith(PROVINCIA['codigo_ine'])
    }
    if {r['codi'] for r in rows} != idescat:
        raise SystemExit('Generalitat and Idescat municipality lists differ; aborting.')
    if len(rows) != EXPECTED_MUNICIPIOS:
        raise SystemExit(f'Expected {EXPECTED_MUNICIPIOS} municipalities, got {len(rows)}.')

    comarcas = {}
    municipios = []
    for r in rows:
        comarcas[r['codi_comarca']] = r['nom_comarca']
        municipios.append({
            # Idescat/Generalitat codes carry a 6th check digit; INE uses the first five.
            'codigo_ine': r['codi'][:5],
            'nombre': fix_article(r['nom']),
            'comarca': r['codi_comarca'],
            'latitud': round(float(r['latitud']), 6),
            'longitud': round(float(r['longitud']), 6),
        })
    municipios.sort(key=lambda m: m['codigo_ine'])

    distritos = [
        {
            'municipio_ine': BARCELONA_INE,
            'codigo': row['Codi_Districte'],
            'nombre': row['nom_districte'],
        }
        for row in csv.DictReader(io.StringIO(_get(SRC_BCN_DISTRITOS)))
    ]

    barrios = [
        {
            'municipio_ine': BARCELONA_INE,
            'distrito': row['codi_districte'],
            'codigo': row['codi_barri'],
            'nombre': row['nom_barri'],
        }
        for row in csv.DictReader(io.StringIO(_get(SRC_BCN_BARRIOS)))
    ]
    if len(barrios) != EXPECTED_BARRIOS_BCN:
        raise SystemExit(f'Expected {EXPECTED_BARRIOS_BCN} barrios, got {len(barrios)}.')
    known = {d['codigo'] for d in distritos}
    if {b['distrito'] for b in barrios} - known:
        raise SystemExit('A barrio refers to an unknown distrito; aborting.')

    _write('provincias', [], [PROVINCIA])
    _write('comarcas', [SRC_MUNICIPIOS], [
        {'codigo': c, 'nombre': n} for c, n in sorted(comarcas.items())
    ])
    _write('municipios', [SRC_MUNICIPIOS, SRC_IDESCAT], municipios)
    _write('distritos', [SRC_BCN_DISTRITOS], distritos)
    _write('barrios', [SRC_BCN_BARRIOS], barrios)
