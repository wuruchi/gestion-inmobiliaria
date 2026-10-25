"""Load the main agency (AtBarcelona, ATB) from data/agencia.json.

Staff edit the agency in the admin, so this only creates what is missing and never overwrites.
"""
import json

from django.db import transaction

from .fetch import DATA_DIR
from .locations import DryRun

CAMPOS = ('siglas', 'aicat', 'numero_api', 'direccion', 'telefono', 'email')


def seed_agencia(dry_run=False):
    """Returns `{'Agencia': [created, kept]}`."""
    from base.models import Agencia

    items = json.loads((DATA_DIR / 'agencia.json').read_text(encoding='utf-8'))['items']
    created = kept = 0
    try:
        with transaction.atomic():
            for item in items:
                if Agencia.objects.filter(nombre=item['nombre']).exists():
                    kept += 1
                    continue
                if item['aicat'] and Agencia.objects.filter(aicat=item['aicat']).exists():
                    kept += 1  # another agency already holds this AICAT: staff's data wins
                else:
                    Agencia.objects.create(nombre=item['nombre'], **{c: item.get(c, '') for c in CAMPOS})
                    created += 1
            if dry_run:
                raise DryRun
    except DryRun:
        pass
    return {'Agencia': [created, kept]}
