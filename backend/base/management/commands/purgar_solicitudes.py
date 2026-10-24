from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from base.models import SolicitudReserva

DEFAULT_MONTHS = 12


class Command(BaseCommand):
    help = (
        'Blank nombre, email and telefono on reservation requests older than the retention '
        'period (default 12 months of 30 days). The rows stay, for statistics. Safe to run '
        'repeatedly, for example from cron.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--meses', type=int, default=DEFAULT_MONTHS)
        parser.add_argument('--dry-run', action='store_true', help='Only count, change nothing.')

    def handle(self, *args, meses, dry_run, **options):
        if meses < 1:
            self.stderr.write('--meses must be at least 1')
            return
        cutoff = timezone.now() - timedelta(days=30 * meses)
        old = SolicitudReserva.objects.filter(created_at__lt=cutoff, datos_borrados__isnull=True)
        count = old.count()
        if not dry_run:
            old.update(nombre='', email='', telefono='', datos_borrados=timezone.now())
        verb = 'would blank' if dry_run else 'blanked'
        self.stdout.write(f'{verb} personal data on {count} request(s) older than {meses} month(s)')
