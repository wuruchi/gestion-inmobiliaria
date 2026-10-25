from django.db import migrations, models

# Presence-only items: the count was only ever 0 or 1 in practice (ADR 0010).
DOTACION = ['jacuzzi_hidromasaje', 'secadora', 'lavadora', 'lavavajillas', 'microondas', 'nevera', 'radio', 'toldo', 'horno', 'tendedero']
OTROS_ESPACIOS = ['altillo', 'galeria', 'buhardilla', 'bodega', 'lavadero']


def a_presencia(apps, schema_editor):
    """Clamp the counts to 0/1 first, so converting the column type cannot see other numbers."""
    for modelo, campos in (('Dotacion', DOTACION), ('OtrosEspacios', OTROS_ESPACIOS)):
        Modelo = apps.get_model('base', modelo)
        for campo in campos:
            Modelo.objects.filter(**{f'{campo}__gt': 1}).update(**{campo: 1})


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0029_quitar_otros_office'),
    ]

    operations = [
        migrations.RunPython(a_presencia, migrations.RunPython.noop),
        migrations.AlterField(model_name='dotacion', name='jacuzzi_hidromasaje', field=models.BooleanField(default=False)),
        migrations.AlterField(model_name='dotacion', name='secadora', field=models.BooleanField(default=False)),
        migrations.AlterField(model_name='dotacion', name='lavadora', field=models.BooleanField(default=False)),
        migrations.AlterField(model_name='dotacion', name='lavavajillas', field=models.BooleanField(default=False)),
        migrations.AlterField(model_name='dotacion', name='microondas', field=models.BooleanField(default=False)),
        migrations.AlterField(model_name='dotacion', name='nevera', field=models.BooleanField(default=False)),
        migrations.AlterField(model_name='dotacion', name='radio', field=models.BooleanField(default=False)),
        migrations.AlterField(model_name='dotacion', name='toldo', field=models.BooleanField(default=False)),
        migrations.AlterField(model_name='dotacion', name='horno', field=models.BooleanField(default=False)),
        migrations.AlterField(model_name='dotacion', name='tendedero', field=models.BooleanField(default=False)),
        migrations.AlterField(model_name='otrosespacios', name='altillo', field=models.BooleanField(default=False)),
        migrations.AlterField(model_name='otrosespacios', name='galeria', field=models.BooleanField(default=False)),
        migrations.AlterField(model_name='otrosespacios', name='buhardilla', field=models.BooleanField(default=False)),
        migrations.AlterField(model_name='otrosespacios', name='bodega', field=models.BooleanField(default=False)),
        migrations.AlterField(model_name='otrosespacios', name='lavadero', field=models.BooleanField(default=False)),
    ]
