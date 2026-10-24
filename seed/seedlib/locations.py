"""Load provincias, comarcas, municipios, distritos and barrios from data/*.json (idempotent)."""
import json

from django.db import transaction
from django.utils.text import slugify

from .fetch import DATA_DIR


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

    A municipio's code must start with the code of a province in the files, its comarca must exist,
    and every distrito and barrio must point at a municipio / distrito that is in the files.
    A comarca has no province of its own (Cerdanya spans two), so it may group municipios of
    several provinces; a `provincia` key on a comarca is stale and reported.
    """
    provincias = {p['codigo_ine'] for p in _load('provincias')}
    comarcas = {c['codigo'] for c in _load('comarcas')}
    problems = [
        f'comarca {c["codigo"]}: has a provincia, but a comarca belongs to none'
        for c in _load('comarcas') if 'provincia' in c
    ]
    municipios = {}
    for m in _load('municipios'):
        code = m['codigo_ine']
        municipios[code] = code[:2]
        if code[:2] not in provincias:
            problems.append(f'municipio {code}: unknown provincia {code[:2]}')
        if m['comarca'] not in comarcas:
            problems.append(f'municipio {code}: unknown comarca {m["comarca"]}')
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
                    {'codigo': c['codigo']},
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


def check_locations():
    """Run the backend's location consistency scan; returns the list of `(tipo, descripcion)` problems."""
    from base.comprobaciones import inconsistencias_ubicacion
    return inconsistencias_ubicacion()
