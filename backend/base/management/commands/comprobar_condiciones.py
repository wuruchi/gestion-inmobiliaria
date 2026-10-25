from django.core.management.base import BaseCommand, CommandError

from base.comprobaciones import inconsistencias_condiciones


class Command(BaseCommand):
    help = (
        'Check that every offer\'s conditions belong to the offer\'s own modalidad. Lists the offenders '
        'and fails if there are any. Read only; safe to run from cron or after a bulk import.'
    )

    def handle(self, *args, **options):
        problemas = inconsistencias_condiciones()
        for tipo, descripcion in problemas:
            self.stdout.write(f'{tipo}: {descripcion}')
        if problemas:
            raise CommandError(f'{len(problemas)} condition problem(s) found')
        self.stdout.write('conditions are consistent')
