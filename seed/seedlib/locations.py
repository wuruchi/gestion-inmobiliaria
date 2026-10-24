"""Load provincias, comarcas, municipios, distritos and barrios from data/*.json (idempotent)."""
import json

from django.db import transaction
from django.utils.text import slugify

from .fetch import DATA_DIR


DEFAULT_PROVINCIA = '08'  # the comarca file does not name its province: Catalonia's is Barcelona's


class DryRun(Exception):
    pass


def _load(name):
    return json.loads((DATA_DIR / f'{name}.json').read_text(encoding='utf-8'))['items']


def _upsert(model, lookup, defaults, stats):
    obj, created = model.objects.update_or_create(defaults=defaults, **lookup)
    stats.setdefault(model.__name__, [0, 0])[0 if created else 1] += 1
    return obj


def validate_locations():
    """Check that the data files nest properly; returns the list of problems (empty = ok).

    A municipio's code must start with its province's, its comarca must exist, and every
    distrito and barrio must point at a municipio / distrito that is in the files.
    """
    provincias = {p['codigo_ine'] for p in _load('provincias')}
    comarcas = {c['codigo']: c.get('provincia', DEFAULT_PROVINCIA) for c in _load('comarcas')}
    problems = [
        f'comarca {code}: unknown provincia {prov}'
        for code, prov in comarcas.items() if prov not in provincias
    ]
    municipios = {}
    for m in _load('municipios'):
        code = m['codigo_ine']
        municipios[code] = code[:2]
        if code[:2] not in provincias:
            problems.append(f'municipio {code}: unknown provincia {code[:2]}')
        if m['comarca'] not in comarcas:
            problems.append(f'municipio {code}: unknown comarca {m["comarca"]}')
        elif comarcas[m['comarca']] != code[:2]:
            problems.append(f'municipio {code}: comarca {m["comarca"]} is in another provincia')
    distritos = set()
    for d in _load('distritos'):
        if d['municipio_ine'] not in municipios:
            problems.append(f'distrito {d["codigo"]}: unknown municipio {d["municipio_ine"]}')
        distritos.add((d['municipio_ine'], d['codigo']))
    for b in _load('barrios'):
        if (b['municipio_ine'], b['distrito']) not in distritos:
            problems.append(
                f'barrio {b["codigo"]}: unknown distrito {b["municipio_ine"]}/{b["distrito"]}'
            )
    return problems


def seed_locations(dry_run=False):
    from base.models import Barrio, Comarca, Distrito, Municipio, Provincia

    problems = validate_locations()
    if problems:
        raise ValueError('Invalid location data:\n  ' + '\n  '.join(problems))
    stats = {}
    try:
        with transaction.atomic():
            provincias = {}
            for p in _load('provincias'):
                provincias[p['codigo_ine']] = _upsert(
                    Provincia,
                    {'codigo_ine': p['codigo_ine']},
                    {'nombre': p['nombre'], 'slug': slugify(p['nombre'])},
                    stats,
                )

            comarcas = {}
            for c in _load('comarcas'):
                comarcas[c['codigo']] = _upsert(
                    Comarca,
                    {
                        'provincia': provincias[c.get('provincia', DEFAULT_PROVINCIA)],
                        'codigo': c['codigo'],
                    },
                    {'nombre': c['nombre'], 'slug': slugify(c['nombre'])},
                    stats,
                )

            municipios = {}
            for m in _load('municipios'):
                municipios[m['codigo_ine']] = _upsert(
                    Municipio,
                    {'codigo_ine': m['codigo_ine']},
                    {
                        'provincia': provincias[m['codigo_ine'][:2]],
                        'comarca': comarcas[m['comarca']],
                        'nombre': m['nombre'],
                        'slug': slugify(m['nombre']),
                        'latitud': m['latitud'],
                        'longitud': m['longitud'],
                    },
                    stats,
                )

            distritos = {}
            for d in _load('distritos'):
                distritos[(d['municipio_ine'], d['codigo'])] = _upsert(
                    Distrito,
                    {'municipio': municipios[d['municipio_ine']], 'codigo': d['codigo']},
                    {'nombre': d['nombre'], 'slug': slugify(d['nombre'])},
                    stats,
                )
            for b in _load('barrios'):
                _upsert(
                    Barrio,
                    {'distrito': distritos[(b['municipio_ine'], b['distrito'])], 'codigo': b['codigo']},
                    {'nombre': b['nombre'], 'slug': slugify(b['nombre'])},
                    stats,
                )
            if dry_run:
                raise DryRun
    except DryRun:
        pass
    return stats
