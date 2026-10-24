from django.db import migrations

CAMPOS_CONDICIONES = (
    'fianza', 'honorarios', 'pago_adelantado', 'itp', 'suministros',
    'limpieza_final', 'incluido', 'no_incluido',
)


def copiar_condiciones(apps, schema_editor):
    """Each old record becomes one `Condiciones` per modalidad it applied to.

    The default record applied to every modalidad. Any other record applied to the
    modalidades of the listings that used it (the first modalidad if none did).
    """
    Antiguas = apps.get_model('base', 'CondicionesAlquiler')
    Condiciones = apps.get_model('base', 'Condiciones')
    Modalidad = apps.get_model('base', 'Modalidad')
    InmuebleModalidad = apps.get_model('base', 'InmuebleModalidad')
    todas = list(Modalidad.objects.order_by('orden', 'codigo'))
    for vieja in Antiguas.objects.all():
        if vieja.por_defecto:
            modalidades = todas
        else:
            usadas = set(
                InmuebleModalidad.objects.filter(inmueble__condiciones=vieja)
                .values_list('modalidad_id', flat=True)
            )
            modalidades = [m for m in todas if m.pk in usadas] or todas[:1]
        if not modalidades:
            raise RuntimeError(
                f'Load the modalidades (seed) before migrating: conditions "{vieja.nombre}" need one.'
            )
        for modalidad in modalidades:
            nueva = Condiciones.objects.create(
                nombre=vieja.nombre if len(modalidades) == 1 else f'{vieja.nombre} ({modalidad.nombre})',
                modalidad=modalidad,
                por_defecto=vieja.por_defecto,
                **{campo: getattr(vieja, campo) for campo in CAMPOS_CONDICIONES},
            )
            InmuebleModalidad.objects.filter(
                inmueble__condiciones=vieja, modalidad=modalidad
            ).update(condiciones=nueva)


def copiar_historial(apps, schema_editor):
    """Old rent history belongs to the listing's monthly modalidad."""
    Historial = apps.get_model('base', 'HistorialRenta')
    HistorialPrecio = apps.get_model('base', 'HistorialPrecio')
    Modalidad = apps.get_model('base', 'Modalidad')
    InmuebleModalidad = apps.get_model('base', 'InmuebleModalidad')
    mensual = Modalidad.objects.filter(unidad_precio='mensual').order_by('orden', 'codigo').first()
    for renta in Historial.objects.all():
        propia = (
            InmuebleModalidad.objects.filter(inmueble_id=renta.inmueble_id, modalidad__unidad_precio='mensual')
            .order_by('modalidad__orden', 'modalidad__codigo').first()
        )
        modalidad_id = propia.modalidad_id if propia else (mensual.pk if mensual else None)
        if modalidad_id is None:
            raise RuntimeError('Load a monthly modalidad (seed) before migrating the rent history.')
        HistorialPrecio.objects.create(
            inmueble_id=renta.inmueble_id, modalidad_id=modalidad_id,
            fecha=renta.fecha, importe=renta.importe, nota=renta.nota,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0008_precio_condiciones_historial'),
    ]

    operations = [
        migrations.RunPython(copiar_condiciones, migrations.RunPython.noop),
        migrations.RunPython(copiar_historial, migrations.RunPython.noop),
    ]
