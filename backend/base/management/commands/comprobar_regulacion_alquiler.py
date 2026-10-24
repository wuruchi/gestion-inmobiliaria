from django.core.management.base import BaseCommand, CommandError

from base.comprobaciones import pendientes_regulacion_alquiler


class Command(BaseCommand):
    help = (
        'List the published habitual-rent offers in a stressed zone that lack the reference index or the '
        'last-rent information (unconfirmed, no end date, or older than 5 years), and fail if there are any. '
        'Read only; safe to run from cron or before publishing.'
    )

    def handle(self, *args, **options):
        problemas = pendientes_regulacion_alquiler()
        for tipo, descripcion in problemas:
            self.stdout.write(f'{tipo}: {descripcion}')
        if problemas:
            raise CommandError(f'{len(problemas)} rent-regulation problem(s) found')
        self.stdout.write('rent regulation data is complete')
