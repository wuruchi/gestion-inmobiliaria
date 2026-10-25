from django.db import migrations, models

ANTES = {'Vivienda': 'vivienda', 'Oficina': 'oficina', 'Local': 'local', 'Parking': 'parking', 'Otro': 'otro'}
CHOICES = [('vivienda', 'Vivienda'), ('oficina', 'Oficina'), ('local', 'Local'), ('parking', 'Parking'), ('otro', 'Otro')]


def a_minusculas(apps, schema_editor):
    """Known values map one to one; anything else becomes `otro`."""
    Inmueble = apps.get_model('base', 'Inmueble')
    for antes, despues in ANTES.items():
        Inmueble.objects.filter(tipo=antes).update(tipo=despues)
    Inmueble.objects.exclude(tipo__in=ANTES.values()).update(tipo='otro')


def a_capitalizado(apps, schema_editor):
    Inmueble = apps.get_model('base', 'Inmueble')
    for antes, despues in ANTES.items():
        Inmueble.objects.filter(tipo=despues).update(tipo=antes)


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0038_contadores_con_n'),
    ]

    operations = [
        migrations.RemoveConstraint(model_name='inmueble', name='inmueble_subtipo_solo_vivienda'),
        migrations.RunPython(a_minusculas, a_capitalizado),
        migrations.AlterField(
            model_name='inmueble',
            name='tipo',
            field=models.CharField(blank=True, choices=CHOICES, default='otro', max_length=50),
        ),
        migrations.AddConstraint(
            model_name='inmueble',
            constraint=models.CheckConstraint(condition=models.Q(('subtipo', ''), ('tipo', 'vivienda'), _connector='OR'), name='inmueble_subtipo_solo_vivienda'),
        ),
    ]
