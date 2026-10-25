#!/usr/bin/env python
"""Seed tool for the AtBarcelona database.

    python seed.py migrate            apply the backend's migrations
    python seed.py locations          load provincias/comarcas/municipios/distritos/barrios
    python seed.py locations --dry-run
    python seed.py modalidades        load the three Modalidad rows (also supports --dry-run)
    python seed.py condiciones        create the default Condiciones of each modalidad (also supports --dry-run)
    python seed.py zonas-tensionadas  load the stressed-zone declarations of the municipios already loaded (also supports --dry-run)
    python seed.py check-locations    check that listings' locations nest (read only)
    python seed.py status             row counts
    python seed.py fetch-locations    refresh data/*.json from the official sources

The backend project is found through ATB_BACKEND_PATH (default ../backend);
the database is chosen by the same DB_* environment variables the backend uses.
"""
import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def setup_django():
    backend = Path(os.environ.get('ATB_BACKEND_PATH', HERE.parent / 'backend')).resolve()
    if not (backend / 'base').is_dir():
        sys.exit(f'Backend not found at {backend}; set ATB_BACKEND_PATH.')
    sys.path[:0] = [str(backend), str(HERE)]
    os.environ['DJANGO_SETTINGS_MODULE'] = 'seedlib.settings'
    import django
    django.setup()
    from django.conf import settings
    return settings.DATABASES['default']['NAME']


def report_location_consistency():
    """Print the backend's location scan; the exit status is 1 when something does not nest."""
    from seedlib.locations import check_locations
    problems = check_locations()
    for tipo, descripcion in problems:
        print(f'{tipo}: {descripcion}')
    print(f'location check: {len(problems)} problem(s)' if problems else 'location check: consistent')
    return 1 if problems else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('migrate')
    loc = sub.add_parser('locations')
    loc.add_argument('--dry-run', action='store_true', help='report what would change, write nothing')
    mod = sub.add_parser('modalidades')
    mod.add_argument('--dry-run', action='store_true', help='report what would change, write nothing')
    con = sub.add_parser('condiciones')
    con.add_argument('--dry-run', action='store_true', help='report what would change, write nothing')
    zon = sub.add_parser('zonas-tensionadas')
    zon.add_argument('--dry-run', action='store_true', help='report what would change, write nothing')
    sub.add_parser('check-locations')
    sub.add_parser('status')
    sub.add_parser('fetch-locations')
    args = parser.parse_args()

    if args.command == 'fetch-locations':
        sys.path.insert(0, str(HERE))
        from seedlib.fetch import fetch_locations
        return fetch_locations()

    database = setup_django()
    print(f'database: {database}')
    if args.command == 'migrate':
        from django.core.management import call_command
        call_command('migrate', 'base', verbosity=1)
    elif args.command == 'locations':
        from seedlib.locations import seed_locations
        for model, (created, updated) in seed_locations(args.dry_run).items():
            print(f'{model:10} created {created:4}  updated {updated:4}')
        if args.dry_run:
            print('dry run: nothing was written')
        else:
            return report_location_consistency()
    elif args.command == 'check-locations':
        return report_location_consistency()
    elif args.command == 'modalidades':
        from seedlib.modalidades import seed_modalidades
        for model, (created, updated) in seed_modalidades(args.dry_run).items():
            print(f'{model:10} created {created:4}  updated {updated:4}')
        if args.dry_run:
            print('dry run: nothing was written')
    elif args.command == 'condiciones':
        from seedlib.condiciones import seed_condiciones
        for model, (created, kept) in seed_condiciones(args.dry_run).items():
            print(f'{model:12} created {created:4}  kept {kept:4}')
        if args.dry_run:
            print('dry run: nothing was written')
    elif args.command == 'zonas-tensionadas':
        from seedlib.zonas_tensionadas import seed_zonas_tensionadas
        stats, sin_cargar = seed_zonas_tensionadas(args.dry_run)
        for referencia, (created, kept) in stats.items():
            print(f'{referencia}: created {created:4}  kept {kept:4}  not loaded {len(sin_cargar[referencia]):4}')
            if sin_cargar[referencia]:
                print('  municipios not in the database: ' + ', '.join(sin_cargar[referencia]))
        if args.dry_run:
            print('dry run: nothing was written')
    elif args.command == 'status':
        from base.models import (
            Barrio, Comarca, Condiciones, DeclaracionZonaTensionada, Distrito, Inmueble, Modalidad, Municipio, Provincia,
        )
        for model in (Provincia, Comarca, Municipio, Distrito, Barrio, Modalidad, Condiciones,
                      DeclaracionZonaTensionada, Inmueble):
            print(f'{model.__name__:10} {model.objects.count()}')


if __name__ == '__main__':
    sys.exit(main() or 0)
