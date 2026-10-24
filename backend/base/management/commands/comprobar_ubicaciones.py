from django.core.management.base import BaseCommand, CommandError

from base.comprobaciones import inconsistencias_ubicacion


class Command(BaseCommand):
    help = (
        'Check that every listing\'s municipio, distrito and barrio nest, and that every municipio '
        'code starts with its province\'s. Lists the offenders and fails if there are any. '
        'Read only; safe to run from cron or after a bulk import.'
    )

    def handle(self, *args, **options):
        problemas = inconsistencias_ubicacion()
        for tipo, descripcion in problemas:
            self.stdout.write(f'{tipo}: {descripcion}')
        if problemas:
            raise CommandError(f'{len(problemas)} location problem(s) found')
        self.stdout.write('locations are consistent')
