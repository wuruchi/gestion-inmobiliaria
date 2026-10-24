import django.db.models.deletion
from django.db import migrations, models


def check_locations(apps, schema_editor):
    """Stop, listing the offenders, instead of guessing a location."""
    Inmueble = apps.get_model('base', 'Inmueble')
    Distrito = apps.get_model('base', 'Distrito')
    Barrio = apps.get_model('base', 'Barrio')
    problems = []
    for inm in Inmueble.objects.select_related('municipio'):
        if inm.municipio_id is None:
            problems.append(f'{inm.referencia}: no municipio')
        elif inm.provincia_id and inm.municipio.provincia_id != inm.provincia_id:
            problems.append(f'{inm.referencia}: provincia differs from the municipio\'s')
        if inm.distrito_id and Distrito.objects.get(pk=inm.distrito_id).municipio_id != inm.municipio_id:
            problems.append(f'{inm.referencia}: distrito not in the municipio')
        if inm.barrio_id:
            barrio_distrito = Barrio.objects.get(pk=inm.barrio_id).distrito_id
            if inm.distrito_id and barrio_distrito != inm.distrito_id:
                problems.append(f'{inm.referencia}: barrio not in the distrito')
    municipio = apps.get_model('base', 'Municipio')
    for m in municipio.objects.select_related('provincia', 'comarca'):
        if not m.codigo_ine.startswith(m.provincia.codigo_ine):
            problems.append(f'municipio {m.codigo_ine}: code does not start with the provincia\'s')
        if m.comarca_id and m.comarca.provincia_id != m.provincia_id:
            problems.append(f'municipio {m.codigo_ine}: comarca in another provincia')
    if problems:
        raise RuntimeError(
            'Fix these locations before migrating:\n  ' + '\n  '.join(problems)
        )


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(check_locations, migrations.RunPython.noop),
        migrations.RemoveIndex(model_name='inmueble', name='inm_web_loc'),
        migrations.RemoveField(model_name='inmueble', name='provincia'),
        migrations.AlterField(
            model_name='inmueble',
            name='municipio',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='base.municipio'),
        ),
        migrations.AlterField(
            model_name='inmueble',
            name='distrito',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='base.distrito'),
        ),
        migrations.AddIndex(
            model_name='inmueble',
            index=models.Index(fields=['publicar_web', 'municipio', 'distrito', 'barrio'], name='inm_web_loc'),
        ),
    ]
