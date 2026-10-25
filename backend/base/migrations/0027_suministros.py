import unicodedata

import django.db.models.deletion
from django.db import migrations, models

AGUA_ELECTRICIDAD_GAS = ['agua', 'electricidad', 'gas']

TIPOS_CALEFACCION = {'central': 'Central', 'individual': 'Individual'}
SUBTIPOS_CALEFACCION = {
    'gas_natural': 'Gas natural', 'electrica': 'Eléctrica', 'gasoleo': 'Gasóleo',
    'biomasa': 'Biomasa', 'aerotermia': 'Aerotermia', 'otro': 'Otro',
}
TIPOS_GAS = {'natural': 'Gas natural', 'butano': 'Butano', 'propano': 'Propano', 'otro': 'Otro'}


def normalizar(texto):
    sin_tildes = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return sin_tildes.strip().lower().replace(' ', '_')


def a_valor(texto, validos):
    """Map free text to a choice value; unknown text becomes 'otro' where it exists, else ''."""
    clave = normalizar(texto)
    if not clave:
        return ''
    if clave in validos:
        return clave
    if clave in ('gas', 'gas_ciudad', 'natural', 'gas_natural'):
        return 'gas_natural' if 'gas_natural' in validos else 'natural'
    return 'otro' if 'otro' in validos else ''


def a_suministros(apps, schema_editor):
    Instalaciones = apps.get_model('base', 'Instalaciones')
    Suministro = apps.get_model('base', 'Suministro')
    for i in Instalaciones.objects.all().iterator():
        i.tipo_calefaccion = a_valor(i.tipo_calefaccion, TIPOS_CALEFACCION)
        i.subtipo_calefaccion = a_valor(i.subtipo_calefaccion, SUBTIPOS_CALEFACCION)
        i.save(update_fields=['tipo_calefaccion', 'subtipo_calefaccion'])
        for tipo in AGUA_ELECTRICIDAD_GAS:
            contador = getattr(i, f'contador_{tipo}')
            compania = getattr(i, f'compania_{tipo}')
            tipo_suministro = a_valor(i.tipo_gas, TIPOS_GAS) if tipo == 'gas' else ''
            existe = contador or compania or (tipo == 'gas' and (i.gas or tipo_suministro))
            if existe:
                Suministro.objects.create(
                    inmueble_id=i.inmueble_id, tipo=tipo, contador=contador,
                    compania=compania, tipo_suministro=tipo_suministro)


def a_columnas(apps, schema_editor):
    Instalaciones = apps.get_model('base', 'Instalaciones')
    Suministro = apps.get_model('base', 'Suministro')
    for i in Instalaciones.objects.all().iterator():
        i.tipo_calefaccion = TIPOS_CALEFACCION.get(i.tipo_calefaccion, i.tipo_calefaccion)
        i.subtipo_calefaccion = SUBTIPOS_CALEFACCION.get(i.subtipo_calefaccion, i.subtipo_calefaccion)
        i.save(update_fields=['tipo_calefaccion', 'subtipo_calefaccion'])
    for s in Suministro.objects.all().iterator():
        i, _ = Instalaciones.objects.get_or_create(inmueble_id=s.inmueble_id)
        setattr(i, f'contador_{s.tipo}', s.contador)
        setattr(i, f'compania_{s.tipo}', s.compania)
        if s.tipo == 'gas':
            i.gas = True
            i.tipo_gas = TIPOS_GAS.get(s.tipo_suministro, s.tipo_suministro)
        i.save()


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0026_transporte_por_modo'),
    ]

    operations = [
        migrations.CreateModel(
            name='Suministro',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('agua', 'Agua'), ('electricidad', 'Electricidad'), ('gas', 'Gas')], max_length=20)),
                ('contador', models.BooleanField(default=False, help_text='Tiene contador propio.')),
                ('compania', models.CharField(blank=True, default='', max_length=150)),
                ('tipo_suministro', models.CharField(blank=True, choices=[('natural', 'Gas natural'), ('butano', 'Butano'), ('propano', 'Propano'), ('otro', 'Otro')], default='', help_text='Solo para el gas.', max_length=20)),
                ('inmueble', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='suministros', to='base.inmueble')),
            ],
            options={
                'verbose_name': 'suministro',
                'verbose_name_plural': 'suministros',
                'ordering': ['inmueble', 'tipo'],
                'constraints': [
                    models.UniqueConstraint(fields=('inmueble', 'tipo'), name='uniq_suministro_inmueble_tipo'),
                    models.CheckConstraint(condition=models.Q(('tipo_suministro', ''), ('tipo', 'gas'), _connector='OR'), name='suministro_tipo_suministro_solo_gas'),
                ],
            },
        ),
        migrations.RunPython(a_suministros, a_columnas),
        migrations.RemoveField(model_name='instalaciones', name='contador_agua'),
        migrations.RemoveField(model_name='instalaciones', name='compania_agua'),
        migrations.RemoveField(model_name='instalaciones', name='contador_electricidad'),
        migrations.RemoveField(model_name='instalaciones', name='compania_electricidad'),
        migrations.RemoveField(model_name='instalaciones', name='gas'),
        migrations.RemoveField(model_name='instalaciones', name='tipo_gas'),
        migrations.RemoveField(model_name='instalaciones', name='contador_gas'),
        migrations.RemoveField(model_name='instalaciones', name='compania_gas'),
        migrations.AlterField(
            model_name='instalaciones', name='tipo_calefaccion',
            field=models.CharField(blank=True, choices=[('central', 'Central'), ('individual', 'Individual')], default='', max_length=20),
        ),
        migrations.AlterField(
            model_name='instalaciones', name='subtipo_calefaccion',
            field=models.CharField(blank=True, choices=[('gas_natural', 'Gas natural'), ('electrica', 'Eléctrica'), ('gasoleo', 'Gasóleo'), ('biomasa', 'Biomasa'), ('aerotermia', 'Aerotermia'), ('otro', 'Otro')], default='', max_length=20),
        ),
    ]
