"""Load the Modalidad rows from data/modalidades.json (idempotent)."""
import json

from django.db import transaction

from .fetch import DATA_DIR
from .locations import DryRun


def seed_modalidades(dry_run=False):
    from base.models import Modalidad

    items = json.loads((DATA_DIR / 'modalidades.json').read_text(encoding='utf-8'))['items']
    stats = {'Modalidad': [0, 0]}
    try:
        with transaction.atomic():
            for item in items:
                _, created = Modalidad.objects.update_or_create(
                    codigo=item['codigo'],
                    defaults={'nombre': item['nombre'], 'orden': item['orden']},
                )
                stats['Modalidad'][0 if created else 1] += 1
            if dry_run:
                raise DryRun
    except DryRun:
        pass
    return stats
