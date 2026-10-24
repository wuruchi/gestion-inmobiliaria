from django.db import migrations, models


def a_otros(apps, schema_editor):
    Inmueble = apps.get_model('base', 'Inmueble')
    Otros = apps.get_model('base', 'Otros')
    for pk in Inmueble.objects.filter(ibi_incluido=True).values_list('pk', flat=True):
        Otros.objects.update_or_create(inmueble_id=pk, defaults={'ibi_incluido': True})


def a_inmueble(apps, schema_editor):
    Inmueble = apps.get_model('base', 'Inmueble')
    Otros = apps.get_model('base', 'Otros')
    ids = Otros.objects.filter(ibi_incluido=True).values_list('inmueble_id', flat=True)
    Inmueble.objects.filter(pk__in=list(ids)).update(ibi_incluido=True)


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0006_ajustes_campos_existentes'),
    ]

    operations = [
        migrations.AddField(
            model_name='otros',
            name='ibi_incluido',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(a_otros, a_inmueble),
        migrations.RemoveField(
            model_name='inmueble',
            name='ibi_incluido',
        ),
    ]
