import django.db.models.deletion
from django.db import migrations, models


def a_acuerdos(apps, schema_editor):
    """Each `DatosInternos` with agreement data gets one agreement; `cat_nrc` becomes `referencia_catastral`."""
    Datos = apps.get_model('base', 'DatosInternos')
    Acuerdo = apps.get_model('base', 'AcuerdoAdministracion')
    Inmueble = apps.get_model('base', 'Inmueble')
    for d in Datos.objects.all():
        if d.fecha_firma or d.exclusiva or d.gestion_comercial or d.administracion:
            Acuerdo.objects.create(
                inmueble_id=d.inmueble_id, fecha_firma=d.fecha_firma, exclusiva=d.exclusiva,
                gestion_comercial=d.gestion_comercial, administracion=d.administracion,
            )
        if d.cat_nrc:
            Inmueble.objects.filter(pk=d.inmueble_id).update(referencia_catastral=d.cat_nrc)


def a_datos_internos(apps, schema_editor):
    """Back to one agreement per listing: the most recent one."""
    Datos = apps.get_model('base', 'DatosInternos')
    Acuerdo = apps.get_model('base', 'AcuerdoAdministracion')
    Inmueble = apps.get_model('base', 'Inmueble')
    vistos = set()
    for a in Acuerdo.objects.order_by('-fecha_firma', '-id'):
        if a.inmueble_id in vistos:
            continue
        vistos.add(a.inmueble_id)
        Datos.objects.update_or_create(inmueble_id=a.inmueble_id, defaults={
            'fecha_firma': a.fecha_firma, 'exclusiva': a.exclusiva,
            'gestion_comercial': a.gestion_comercial, 'administracion': a.administracion,
        })
    for i in Inmueble.objects.exclude(referencia_catastral=''):
        Datos.objects.update_or_create(inmueble_id=i.pk, defaults={'cat_nrc': i.referencia_catastral})


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0035_certificado_energetico'),
    ]

    operations = [
        migrations.CreateModel(
            name='AcuerdoAdministracion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_firma', models.DateField(blank=True, help_text='Vacío si se desconoce.', null=True)),
                ('fecha_fin', models.DateField(blank=True, help_text='Vacío si sigue vigente.', null=True)),
                ('exclusiva', models.BooleanField(default=False, help_text='La agencia tiene la exclusiva.')),
                ('gestion_comercial', models.BooleanField(default=False)),
                ('administracion', models.BooleanField(default=False)),
                ('inmueble', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='acuerdos_administracion', to='base.inmueble')),
            ],
            options={
                'verbose_name': 'acuerdo de administración',
                'verbose_name_plural': 'acuerdos de administración',
                'ordering': ['-fecha_firma', '-id'],
                'constraints': [
                    models.CheckConstraint(condition=models.Q(('fecha_firma__isnull', True), ('fecha_fin__isnull', True), ('fecha_fin__gte', models.F('fecha_firma')), _connector='OR'), name='acuerdo_fin_no_antes_de_firma', violation_error_message='El acuerdo no puede terminar antes de firmarse.'),
                ],
            },
        ),
        migrations.AddField(
            model_name='inmueble',
            name='referencia_catastral',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
        migrations.AddField(
            model_name='datosinternos',
            name='fecha_tasacion',
            field=models.DateField(blank=True, help_text='Cuándo dio el propietario ese valor.', null=True, verbose_name='fecha de la tasación'),
        ),
        migrations.AddConstraint(
            model_name='datosinternos',
            constraint=models.CheckConstraint(condition=models.Q(('fecha_tasacion__isnull', True), ('tasacion_propietario__isnull', False), _connector='OR'), name='datos_internos_fecha_tasacion_con_importe', violation_error_message='La fecha de la tasación necesita un importe.'),
        ),
        migrations.RunPython(a_acuerdos, a_datos_internos),
        migrations.RemoveField(model_name='datosinternos', name='cat_nrc'),
        migrations.RemoveField(model_name='datosinternos', name='fecha_firma'),
        migrations.RemoveField(model_name='datosinternos', name='exclusiva'),
        migrations.RemoveField(model_name='datosinternos', name='gestion_comercial'),
        migrations.RemoveField(model_name='datosinternos', name='administracion'),
    ]
