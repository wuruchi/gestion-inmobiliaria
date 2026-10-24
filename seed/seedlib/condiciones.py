"""Load the default Condiciones of each modalidad from data/condiciones.json.

Staff edit these records in the admin, so this only creates what is missing and never
overwrites: a record is skipped when one with that name exists or when the modalidad
already has a default. Needs the modalidades to be loaded first.
"""
import json

from django.db import transaction

from .fetch import DATA_DIR
from .locations import DryRun

TEXTOS = (
    'fianza', 'honorarios', 'pago_adelantado', 'itp', 'suministros', 'actualizacion_renta', 'limpieza_final',
    'incluido', 'no_incluido', 'requisitos', 'notaria', 'registro', 'gestoria',
    'honorarios_comprador',
)


def seed_condiciones(dry_run=False):
    from base.models import Condiciones, Modalidad

    items = json.loads((DATA_DIR / 'condiciones.json').read_text(encoding='utf-8'))['items']
    modalidades = {m.codigo: m for m in Modalidad.objects.all()}
    missing = sorted({i['modalidad'] for i in items} - set(modalidades))
    if missing:
        raise SystemExit(f'Load the modalidades first (python seed.py modalidades); missing: {", ".join(missing)}')
    created = kept = 0
    try:
        with transaction.atomic():
            for item in items:
                modalidad = modalidades[item['modalidad']]
                if (
                    Condiciones.objects.filter(nombre=item['nombre']).exists()
                    or Condiciones.objects.filter(modalidad=modalidad, por_defecto=True).exists()
                ):
                    kept += 1
                    continue
                Condiciones.objects.create(
                    nombre=item['nombre'], modalidad=modalidad, por_defecto=True,
                    **{campo: item[campo] for campo in TEXTOS if campo in item},
                )
                created += 1
            if dry_run:
                raise DryRun
    except DryRun:
        pass
    return {'Condiciones': [created, kept]}
