import django.db.models.deletion
from django.db import migrations, models

MODOS = ['bus', 'metro', 'tranvia', 'tren', 'ferrocarril']


def a_filas(apps, schema_editor):
    Transporte = apps.get_model('base', 'Transporte')
    Fila = apps.get_model('base', 'TransporteInmueble')
    for t in Transporte.objects.all().iterator():
        for modo in MODOS:
            descripcion = getattr(t, f'descripcion_{modo}')
            if getattr(t, f'cerca_{modo}') or descripcion:
                Fila.objects.create(inmueble_id=t.inmueble_id, tipo=modo, descripcion=descripcion)


def a_columnas(apps, schema_editor):
    Transporte = apps.get_model('base', 'Transporte')
    Fila = apps.get_model('base', 'TransporteInmueble')
    for fila in Fila.objects.all().iterator():
        t, _ = Transporte.objects.get_or_create(inmueble_id=fila.inmueble_id)
        setattr(t, f'cerca_{fila.tipo}', True)
        setattr(t, f'descripcion_{fila.tipo}', fila.descripcion)
        t.save()


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0025_descripciones_por_idioma'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransporteInmueble',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('bus', 'Bus'), ('metro', 'Metro'), ('tranvia', 'Tranvía'), ('tren', 'Tren'), ('ferrocarril', 'Ferrocarril')], max_length=20)),
                ('descripcion', models.CharField(blank=True, default='', max_length=150)),
                ('inmueble', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transportes', to='base.inmueble')),
            ],
            options={
                'verbose_name': 'transporte',
                'verbose_name_plural': 'transportes',
                'ordering': ['inmueble', 'tipo'],
                'constraints': [models.UniqueConstraint(fields=('inmueble', 'tipo'), name='uniq_transporte_inmueble_tipo')],
            },
        ),
        migrations.RunPython(a_filas, a_columnas),
        migrations.DeleteModel(name='Transporte'),
    ]
