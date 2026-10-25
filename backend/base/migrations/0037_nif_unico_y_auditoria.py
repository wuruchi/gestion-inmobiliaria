import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
from django.db.models import Count


def sin_nif_repetido(apps, schema_editor):
    """Stop with the repeated NIFs instead of failing on the constraint with no detail."""
    Propietario = apps.get_model('base', 'Propietario')
    repetidos = (
        Propietario.objects.exclude(nif='').values('nif').annotate(n=Count('id')).filter(n__gt=1)
    )
    problemas = []
    for r in repetidos:
        nombres = ', '.join(Propietario.objects.filter(nif=r['nif']).values_list('nombre', flat=True))
        problemas.append(f'{r["nif"]}: {nombres}')
    if problemas:
        raise RuntimeError('Une estos propietarios (mismo NIF) antes de migrar:\n' + '\n'.join(problemas))


def auditoria(modelo):
    """The four audit columns. Existing rows get the migration time, as the real one is unknown."""
    usuario = dict(
        blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL,
        related_name='+', to=settings.AUTH_USER_MODEL,
    )
    return [
        migrations.AddField(model_name=modelo, name='created_by', field=models.ForeignKey(**usuario)),
        migrations.AddField(
            model_name=modelo, name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(model_name=modelo, name='updated_by', field=models.ForeignKey(**usuario)),
        migrations.AddField(
            model_name=modelo, name='updated_at',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('base', '0036_acuerdo_administracion'),
    ]

    operations = [
        migrations.RunPython(sin_nif_repetido, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='propietario',
            constraint=models.UniqueConstraint(condition=models.Q(('nif', ''), _negated=True), fields=('nif',), name='uniq_propietario_nif', violation_error_message='Ya existe un propietario con este NIF.'),
        ),
        migrations.AlterField(
            model_name='propietario',
            name='nif',
            field=models.CharField(blank=True, default='', help_text='Único cuando se indica.', max_length=20),
        ),
        *auditoria('condiciones'),
        *auditoria('inmueblemodalidad'),
        migrations.AlterField(
            model_name='plazaaparcamiento',
            name='valor',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Nota interna: valor de la plaza. No es un precio de oferta.', max_digits=11, null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='plazaaparcamiento',
            name='renta',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Nota interna: renta que paga la plaza. No es un precio de oferta.', max_digits=9, null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
