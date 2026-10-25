from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models
from django.db.models import Case, F, IntegerField, Q, Value, When
from django.db.models.lookups import LessThanOrEqual
import django.db.models.deletion


DIAS_POR_UNIDAD = {'dias': 1, 'meses': 30, 'anios': 365}


def _estancia_en_dias(campo):
    return Case(
        *(When(**{f'{campo}_unidad': unidad}, then=F(campo) * Value(dias)) for unidad, dias in DIAS_POR_UNIDAD.items()),
        output_field=IntegerField(),
    )

OTROS_CAMPOS_QUE_SALEN = [
    'capacidad_personas', 'anio_ultima_reforma', 'gastos_comunidad_incluidos', 'ibi_incluido',
    'acepta_animales', 'estancia_minima', 'estancia_minima_unidad', 'estancia_maxima', 'estancia_maxima_unidad',
]
TERMINOS = ['acepta_animales', 'estancia_minima', 'estancia_minima_unidad', 'estancia_maxima', 'estancia_maxima_unidad']


def repartir(apps, schema_editor):
    Otros = apps.get_model('base', 'Otros')
    Inmueble = apps.get_model('base', 'Inmueble')
    Distribucion = apps.get_model('base', 'Distribucion')
    Oferta = apps.get_model('base', 'InmuebleModalidad')
    Terminos = apps.get_model('base', 'TerminosAlquiler')
    for o in Otros.objects.all().iterator():
        Inmueble.objects.filter(pk=o.inmueble_id).update(
            anio_ultima_reforma=o.anio_ultima_reforma,
            gastos_comunidad_incluidos=o.gastos_comunidad_incluidos,
            ibi_incluido=o.ibi_incluido)
        if o.capacidad_personas:
            d, _ = Distribucion.objects.get_or_create(inmueble_id=o.inmueble_id)
            d.capacidad_personas = o.capacidad_personas
            d.save(update_fields=['capacidad_personas'])
        if o.acepta_animales or o.estancia_minima is not None or o.estancia_maxima is not None:
            # The terms now belong to each rental offer; a listing without one cannot keep them.
            for oferta in Oferta.objects.filter(inmueble_id=o.inmueble_id, modalidad__unidad_precio='mensual'):
                Terminos.objects.get_or_create(
                    oferta=oferta, defaults={campo: getattr(o, campo) for campo in TERMINOS})


def juntar(apps, schema_editor):
    Otros = apps.get_model('base', 'Otros')
    Inmueble = apps.get_model('base', 'Inmueble')
    Distribucion = apps.get_model('base', 'Distribucion')
    Terminos = apps.get_model('base', 'TerminosAlquiler')
    ids = set(Inmueble.objects.filter(
        Q(anio_ultima_reforma__isnull=False) | Q(gastos_comunidad_incluidos=True) | Q(ibi_incluido=True)
    ).values_list('pk', flat=True))
    ids |= set(Distribucion.objects.exclude(capacidad_personas=None).values_list('inmueble_id', flat=True))
    ids |= set(Terminos.objects.values_list('oferta__inmueble_id', flat=True))
    for pk in ids:
        inmueble = Inmueble.objects.get(pk=pk)
        o, _ = Otros.objects.get_or_create(inmueble_id=pk)
        o.anio_ultima_reforma = inmueble.anio_ultima_reforma
        o.gastos_comunidad_incluidos = inmueble.gastos_comunidad_incluidos
        o.ibi_incluido = inmueble.ibi_incluido
        d = Distribucion.objects.filter(inmueble_id=pk).first()
        o.capacidad_personas = (d.capacidad_personas or 0) if d else 0
        t = Terminos.objects.filter(oferta__inmueble_id=pk).order_by('pk').first()
        if t:
            for campo in TERMINOS:
                setattr(o, campo, getattr(t, campo))
        o.save()


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0032_distribucion'),
    ]

    operations = [
        migrations.CreateModel(
            name='TerminosAlquiler',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('acepta_animales', models.BooleanField(default=False)),
                ('estancia_minima', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('estancia_minima_unidad', models.CharField(choices=[('dias', 'Días'), ('meses', 'Meses'), ('anios', 'Años')], default='meses', max_length=10)),
                ('estancia_maxima', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('estancia_maxima_unidad', models.CharField(choices=[('dias', 'Días'), ('meses', 'Meses'), ('anios', 'Años')], default='meses', max_length=10)),
                ('oferta', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='terminos', to='base.inmueblemodalidad')),
            ],
            options={'verbose_name': 'términos del alquiler', 'verbose_name_plural': 'términos del alquiler'},
        ),
        migrations.AddConstraint(
            model_name='terminosalquiler',
            constraint=models.CheckConstraint(
                condition=Q(estancia_minima__isnull=True) | Q(estancia_maxima__isnull=True) | Q(
                    LessThanOrEqual(_estancia_en_dias('estancia_minima'), _estancia_en_dias('estancia_maxima'))),
                name='terminos_estancia_min_max'),
        ),
        migrations.AddField(
            model_name='inmueble', name='anio_ultima_reforma',
            field=models.PositiveSmallIntegerField(blank=True, null=True, validators=[MinValueValidator(1000), MaxValueValidator(2100)], verbose_name='Año de la última reforma'),
        ),
        migrations.AddField(model_name='inmueble', name='gastos_comunidad_incluidos', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='inmueble', name='ibi_incluido', field=models.BooleanField(default=False)),
        migrations.AddConstraint(
            model_name='inmueble',
            constraint=models.CheckConstraint(
                condition=Q(anio_ultima_reforma__isnull=True) | Q(anio_ultima_reforma__gte=1000, anio_ultima_reforma__lte=2100),
                name='inmueble_anio_ultima_reforma_rango'),
        ),
        migrations.AddField(model_name='distribucion', name='capacidad_personas', field=models.PositiveIntegerField(blank=True, null=True)),
        migrations.RunPython(repartir, juntar),
        migrations.RemoveConstraint(model_name='otros', name='otros_estancia_min_max'),
        *[migrations.RemoveField(model_name='otros', name=campo) for campo in OTROS_CAMPOS_QUE_SALEN],
        migrations.RenameModel(old_name='Otros', new_name='Caracteristicas'),
        migrations.AlterModelOptions(
            name='caracteristicas',
            options={'verbose_name': 'características', 'verbose_name_plural': 'características'},
        ),
    ]
