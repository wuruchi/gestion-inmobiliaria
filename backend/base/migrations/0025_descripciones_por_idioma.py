import django.db.models.deletion
from django.db import migrations, models

COLUMNAS = [('descripcion_es', 'es'), ('descripcion_en', 'en'), ('descripcion_cat', 'ca')]


def a_descripciones(apps, schema_editor):
    Inmueble = apps.get_model('base', 'Inmueble')
    Descripcion = apps.get_model('base', 'DescripcionInmueble')
    for inmueble in Inmueble.objects.all().iterator():
        for columna, idioma in COLUMNAS:
            texto = getattr(inmueble, columna)
            if texto:
                Descripcion.objects.create(inmueble=inmueble, idioma=idioma, texto=texto)


def a_columnas(apps, schema_editor):
    Inmueble = apps.get_model('base', 'Inmueble')
    Descripcion = apps.get_model('base', 'DescripcionInmueble')
    columnas = dict((idioma, columna) for columna, idioma in COLUMNAS)
    for d in Descripcion.objects.all().iterator():
        Inmueble.objects.filter(pk=d.inmueble_id).update(**{columnas[d.idioma]: d.texto})


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0024_regulacion_alquiler'),
    ]

    operations = [
        migrations.CreateModel(
            name='DescripcionInmueble',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idioma', models.CharField(choices=[('es', 'Español'), ('en', 'English'), ('ca', 'Català')], max_length=2)),
                ('texto', models.TextField()),
                ('inmueble', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='descripciones', to='base.inmueble')),
            ],
            options={
                'verbose_name': 'descripción',
                'verbose_name_plural': 'descripciones',
                'ordering': ['inmueble', 'idioma'],
                'constraints': [models.UniqueConstraint(fields=('inmueble', 'idioma'), name='uniq_descripcion_inmueble_idioma')],
            },
        ),
        migrations.RunPython(a_descripciones, a_columnas),
        migrations.RemoveField(model_name='inmueble', name='descripcion_es'),
        migrations.RemoveField(model_name='inmueble', name='descripcion_en'),
        migrations.RemoveField(model_name='inmueble', name='descripcion_cat'),
    ]
