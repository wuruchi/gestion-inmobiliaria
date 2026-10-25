"""Load the stressed-zone declarations from data/zonas_tensionadas.json (idempotent, never overwrites)."""
import json
from datetime import date

from django.db import transaction

from .fetch import DATA_DIR
from .locations import DryRun

ARTICULOS = ("la", "el", "les", "els", "l'")
# The list covers every municipality of Catalonia, so those not on it are known not to be stressed.
PROVINCIAS_CATALANAS = ("08", "17", "25", "43")


def clave(nombre):
    """Comparable form of a municipality name: "Bisbal d'Empordà, la" becomes "la bisbal d'empordà"."""
    nombre = nombre.strip()
    for articulo in ARTICULOS:
        sufijo = f', {articulo}'
        if nombre.endswith(sufijo):
            base = nombre[:-len(sufijo)]
            nombre = articulo + base if articulo.endswith("'") else f'{articulo} {base}'
            break
    return nombre.lower()


def seed_zonas_tensionadas(dry_run=False):
    """Create the missing declarations. Returns `(stats, sin_cargar)`.

    `stats` maps each declaration to `[created, kept]`; `sin_cargar` maps it to the names that match no
    municipio in the database (their province is not loaded). A name that matches two municipios aborts.
    A declaration that already exists for a municipio and start date is kept as staff left it.
    Every loaded municipio of Catalonia is marked `declaraciones_cargadas`: the list is complete for it.
    """
    from base.models import DeclaracionZonaTensionada, Municipio

    items = json.loads((DATA_DIR / 'zonas_tensionadas.json').read_text(encoding='utf-8'))['items']
    por_nombre = {}
    for municipio in Municipio.objects.all():
        por_nombre.setdefault(clave(municipio.nombre), []).append(municipio)
    stats, sin_cargar = {}, {}
    try:
        with transaction.atomic():
            for item in items:
                referencia = item['referencia']
                desde = date.fromisoformat(item['desde'])
                hasta = date.fromisoformat(item['hasta']) if item['hasta'] else None
                stats[referencia] = [0, 0]
                sin_cargar[referencia] = []
                for nombre in item['municipios']:
                    encontrados = por_nombre.get(clave(nombre), [])
                    if len(encontrados) > 1:
                        raise ValueError(f'{referencia}: "{nombre}" matches {len(encontrados)} municipios')
                    if not encontrados:
                        sin_cargar[referencia].append(nombre)
                        continue
                    _, created = DeclaracionZonaTensionada.objects.get_or_create(
                        municipio=encontrados[0], desde=desde,
                        defaults={'hasta': hasta, 'referencia': referencia},
                    )
                    stats[referencia][0 if created else 1] += 1
            Municipio.objects.filter(provincia__codigo_ine__in=PROVINCIAS_CATALANAS).update(
                declaraciones_cargadas=True)
            if dry_run:
                raise DryRun
    except DryRun:
        pass
    return stats, sin_cargar
