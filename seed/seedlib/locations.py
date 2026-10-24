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


def seed_locations(dry_run=False):
    from base.models import Barrio, Comarca, Distrito, Municipio, Provincia

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
            provincia = provincias['08']

            comarcas = {}
            for c in _load('comarcas'):
                comarcas[c['codigo']] = _upsert(
                    Comarca,
                    {'provincia': provincia, 'codigo': c['codigo']},
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
