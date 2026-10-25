from django.db import migrations, models
from django.db.models import F, Q


def sin_incoherencias(apps, schema_editor):
    """Stop with the offending references instead of failing on the constraint with no detail."""
    Inmueble = apps.get_model('base', 'Inmueble')
    Dormitorios = apps.get_model('base', 'Dormitorios')
    problemas = []
    for i in Inmueble.objects.filter(sup_util__gt=F('sup_construida')):
        problemas.append(f'{i.referencia}: superficie útil mayor que la construida')
    for i in Inmueble.objects.filter(fecha_baja__lt=F('fecha_alta')):
        problemas.append(f'{i.referencia}: fecha de baja anterior a la de alta')
    for d in Dormitorios.objects.filter(exteriores__gt=F('dobles') + F('individuales')).select_related('inmueble'):
        problemas.append(f'{d.inmueble.referencia}: más dormitorios exteriores que dormitorios')
    if problemas:
        raise RuntimeError('Corrige estos inmuebles antes de migrar:\n' + '\n'.join(problemas))


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0030_presencia_en_vez_de_cantidad'),
    ]

    operations = [
        migrations.RunPython(sin_incoherencias, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='inmueble',
            constraint=models.CheckConstraint(
                condition=Q(sup_util__isnull=True) | Q(sup_construida__isnull=True) | Q(sup_util__lte=F('sup_construida')),
                name='inmueble_sup_util_no_supera_construida',
                violation_error_message='La superficie útil no puede superar la construida.',
            ),
        ),
        migrations.AddConstraint(
            model_name='inmueble',
            constraint=models.CheckConstraint(
                condition=Q(fecha_alta__isnull=True) | Q(fecha_baja__isnull=True) | Q(fecha_baja__gte=F('fecha_alta')),
                name='inmueble_fecha_baja_no_antes_de_alta',
                violation_error_message='La fecha de baja no puede ser anterior a la de alta.',
            ),
        ),
        migrations.AddConstraint(
            model_name='dormitorios',
            constraint=models.CheckConstraint(
                condition=Q(exteriores__lte=F('dobles') + F('individuales')),
                name='dormitorios_exteriores_dentro_del_total',
                violation_error_message='Los dormitorios exteriores no pueden superar el total.',
            ),
        ),
    ]
