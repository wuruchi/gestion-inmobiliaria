from django.db import migrations


def a_media(apps, schema_editor):
    Inmueble = apps.get_model('base', 'Inmueble')
    MediaInmueble = apps.get_model('base', 'MediaInmueble')
    MediaInmueble.objects.bulk_create(
        MediaInmueble(inmueble_id=pk, tipo='tour', url=url, titulo='Matterport')
        for pk, url in Inmueble.objects.exclude(matterport_url='').values_list('pk', 'matterport_url')
    )


def a_inmueble(apps, schema_editor):
    Inmueble = apps.get_model('base', 'Inmueble')
    MediaInmueble = apps.get_model('base', 'MediaInmueble')
    for medio in MediaInmueble.objects.filter(tipo='tour', titulo='Matterport'):
        Inmueble.objects.filter(pk=medio.inmueble_id).update(matterport_url=medio.url)


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0013_imagenes_tipo_y_medios'),
    ]

    operations = [
        migrations.RunPython(a_media, a_inmueble),
    ]
