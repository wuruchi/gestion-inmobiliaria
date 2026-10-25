import re
import unicodedata

from django.db import migrations, models

MATERIALES_SUELO = {
    'parquet': 'Parquet', 'tarima': 'Tarima', 'gres': 'Gres', 'baldosa': 'Baldosa', 'terrazo': 'Terrazo',
    'marmol': 'Mármol', 'microcemento': 'Microcemento', 'hidraulico': 'Hidráulico', 'otro': 'Otro',
}
MATERIALES_CARPINTERIA = {'madera': 'Madera', 'aluminio': 'Aluminio', 'pvc': 'PVC', 'hierro': 'Hierro', 'otro': 'Otro'}
TIPOS_FACHADA = {
    'ladrillo': 'Ladrillo', 'piedra': 'Piedra', 'hormigon': 'Hormigón', 'revoco': 'Revoco',
    'cristal': 'Cristal', 'otro': 'Otro',
}
TIPOS_COCINA = {
    'independiente': 'Independiente', 'americana': 'Americana', 'abierta': 'Abierta', 'office': 'Office',
    'otro': 'Otro',
}
SITUACIONES = {
    'libre': 'Libre', 'ocupado': 'Ocupado', 'alquilado': 'Alquilado',
    'alquiler_vacacional': 'Alquiler vacacional', 'otro': 'Otro',
}

# model -> field -> choices
CAMPOS = {
    'Otros': {'suelo_piso': MATERIALES_SUELO, 'tipo_fachada': TIPOS_FACHADA},
    'Banios': {'suelo': MATERIALES_SUELO},
    'Estancias': {
        'tipo_cocina': TIPOS_COCINA, 'suelo_cocina': MATERIALES_SUELO,
        'carpinteria_interior': MATERIALES_CARPINTERIA, 'carpinteria_exterior': MATERIALES_CARPINTERIA,
    },
    'Inmueble': {'situacion_actual': SITUACIONES},
}

# Cardinal directions; a corner counts as both of its sides.
DIRECCIONES = {
    'norte': ('norte',), 'n': ('norte',), 'sur': ('sur',), 's': ('sur',),
    'este': ('este',), 'e': ('este',), 'oeste': ('oeste',), 'o': ('oeste',),
    'noreste': ('norte', 'este'), 'ne': ('norte', 'este'), 'sureste': ('sur', 'este'), 'se': ('sur', 'este'),
    'suroeste': ('sur', 'oeste'), 'so': ('sur', 'oeste'), 'noroeste': ('norte', 'oeste'), 'no': ('norte', 'oeste'),
}


def normalizar(texto):
    sin_tildes = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return sin_tildes.strip().lower().replace(' ', '_')


def a_valor(texto, validos):
    """Free text to a choice value; text that matches nothing becomes 'otro'."""
    clave = normalizar(texto)
    if not clave:
        return ''
    return clave if clave in validos else 'otro'


def a_opciones(apps, schema_editor):
    for nombre, campos in CAMPOS.items():
        Modelo = apps.get_model('base', nombre)
        for fila in Modelo.objects.all().iterator():
            for campo, validos in campos.items():
                setattr(fila, campo, a_valor(getattr(fila, campo), validos))
            fila.save(update_fields=list(campos))

    Otros = apps.get_model('base', 'Otros')
    for o in Otros.objects.all().iterator():
        lados = set()
        for palabra in re.findall(r'[a-z]+', normalizar(o.orientacion).replace('_', ' ')):
            lados.update(DIRECCIONES.get(palabra, ()))
        o.orientacion_norte = 'norte' in lados
        o.orientacion_sur = 'sur' in lados
        o.orientacion_este = 'este' in lados
        o.orientacion_oeste = 'oeste' in lados
        o.office = bool(o.office_texto.strip())
        o.save(update_fields=[
            'orientacion_norte', 'orientacion_sur', 'orientacion_este', 'orientacion_oeste', 'office'])


def a_texto(apps, schema_editor):
    for nombre, campos in CAMPOS.items():
        Modelo = apps.get_model('base', nombre)
        for fila in Modelo.objects.all().iterator():
            for campo, validos in campos.items():
                valor = getattr(fila, campo)
                setattr(fila, campo, validos.get(valor, valor))
            fila.save(update_fields=list(campos))

    Otros = apps.get_model('base', 'Otros')
    for o in Otros.objects.all().iterator():
        lados = [lado for lado in ('norte', 'sur', 'este', 'oeste') if getattr(o, f'orientacion_{lado}')]
        o.orientacion = ', '.join(lados)
        o.office_texto = 'Sí' if o.office else ''
        o.save(update_fields=['orientacion', 'office_texto'])


def opciones(validos):
    return list(validos.items())


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0027_suministros'),
    ]

    operations = [
        migrations.RenameField(model_name='otros', old_name='office', new_name='office_texto'),
        migrations.AddField(model_name='otros', name='office', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='otros', name='orientacion_norte', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='otros', name='orientacion_sur', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='otros', name='orientacion_este', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='otros', name='orientacion_oeste', field=models.BooleanField(default=False)),
        migrations.RunPython(a_opciones, a_texto),
        migrations.RemoveField(model_name='otros', name='office_texto'),
        migrations.RemoveField(model_name='otros', name='orientacion'),
        migrations.AlterField(model_name='otros', name='suelo_piso', field=models.CharField(blank=True, choices=opciones(MATERIALES_SUELO), default='', max_length=20)),
        migrations.AlterField(model_name='otros', name='tipo_fachada', field=models.CharField(blank=True, choices=opciones(TIPOS_FACHADA), default='', max_length=20)),
        migrations.AlterField(model_name='banios', name='suelo', field=models.CharField(blank=True, choices=opciones(MATERIALES_SUELO), default='', max_length=20)),
        migrations.AlterField(model_name='estancias', name='tipo_cocina', field=models.CharField(blank=True, choices=opciones(TIPOS_COCINA), default='', max_length=20)),
        migrations.AlterField(model_name='estancias', name='suelo_cocina', field=models.CharField(blank=True, choices=opciones(MATERIALES_SUELO), default='', max_length=20)),
        migrations.AlterField(model_name='estancias', name='carpinteria_interior', field=models.CharField(blank=True, choices=opciones(MATERIALES_CARPINTERIA), default='', max_length=20)),
        migrations.AlterField(model_name='estancias', name='carpinteria_exterior', field=models.CharField(blank=True, choices=opciones(MATERIALES_CARPINTERIA), default='', max_length=20)),
        migrations.AlterField(model_name='inmueble', name='situacion_actual', field=models.CharField(blank=True, choices=opciones(SITUACIONES), default='', max_length=20)),
    ]
