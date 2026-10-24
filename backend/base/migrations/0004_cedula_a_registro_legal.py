from django.db import migrations


def copy_cedula(apps, schema_editor):
    Inmueble = apps.get_model('base', 'Inmueble')
    RegistroLegal = apps.get_model('base', 'RegistroLegal')
    RegistroLegal.objects.bulk_create(
        RegistroLegal(inmueble_id=pk, tipo='cedula_habitabilidad', numero=cedula)
        for pk, cedula in Inmueble.objects.exclude(cedula='').values_list('pk', 'cedula')
    )


def restore_cedula(apps, schema_editor):
    Inmueble = apps.get_model('base', 'Inmueble')
    RegistroLegal = apps.get_model('base', 'RegistroLegal')
    for registro in RegistroLegal.objects.filter(tipo='cedula_habitabilidad'):
        Inmueble.objects.filter(pk=registro.inmueble_id).update(cedula=registro.numero[:20])


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_registro_legal_emisiones_ocultar_direccion'),
    ]

    operations = [
        migrations.RunPython(copy_cedula, restore_cedula),
    ]
