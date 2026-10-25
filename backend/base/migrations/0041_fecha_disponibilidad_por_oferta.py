import django.utils.timezone
from django.db import migrations, models


def a_ofertas(apps, schema_editor):
    """Each offer takes its listing's date; without one, the listing's creation date, else today."""
    Inmueble = apps.get_model('base', 'Inmueble')
    Oferta = apps.get_model('base', 'InmuebleModalidad')
    hoy = django.utils.timezone.localdate()
    fechas = {i.pk: i.fecha_disponibilidad or i.fecha_alta or hoy for i in Inmueble.objects.all()}
    for oferta in Oferta.objects.all():
        oferta.fecha_disponibilidad = fechas.get(oferta.inmueble_id, hoy)
        oferta.save(update_fields=['fecha_disponibilidad'])


def a_inmuebles(apps, schema_editor):
    """The listing takes the earliest date of its open offers, else of all its offers."""
    Inmueble = apps.get_model('base', 'Inmueble')
    Oferta = apps.get_model('base', 'InmuebleModalidad')
    for inmueble in Inmueble.objects.all():
        ofertas = list(Oferta.objects.filter(inmueble=inmueble))
        fechas = [o.fecha_disponibilidad for o in ofertas if o.estado != 'cerrado'] or [
            o.fecha_disponibilidad for o in ofertas
        ]
        if fechas:
            Inmueble.objects.filter(pk=inmueble.pk).update(fecha_disponibilidad=min(fechas))


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0040_clave_primaria_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='inmueblemodalidad',
            name='fecha_disponibilidad',
            field=models.DateField(null=True),
        ),
        migrations.RunPython(a_ofertas, a_inmuebles),
        migrations.AlterField(
            model_name='inmueblemodalidad',
            name='fecha_disponibilidad',
            field=models.DateField(default=django.utils.timezone.localdate, help_text='Desde cuándo se puede alquilar o comprar con esta oferta.', verbose_name='disponible desde'),
        ),
        migrations.RemoveIndex(model_name='inmueble', name='inm_web_fecha'),
        migrations.RemoveField(model_name='inmueble', name='fecha_disponibilidad'),
    ]
