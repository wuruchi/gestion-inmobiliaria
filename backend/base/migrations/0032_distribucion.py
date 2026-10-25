from django.db import migrations, models


def banios_a_distribucion(apps, schema_editor):
    Banios = apps.get_model('base', 'Banios')
    Distribucion = apps.get_model('base', 'Distribucion')
    for b in Banios.objects.all().iterator():
        d, _ = Distribucion.objects.get_or_create(inmueble_id=b.inmueble_id)
        d.banios = b.banios
        d.suelo_banio = b.suelo
        d.save(update_fields=['banios', 'suelo_banio'])


def distribucion_a_banios(apps, schema_editor):
    Banios = apps.get_model('base', 'Banios')
    Distribucion = apps.get_model('base', 'Distribucion')
    for d in Distribucion.objects.exclude(banios=None).iterator():
        Banios.objects.update_or_create(inmueble_id=d.inmueble_id, defaults={'banios': d.banios, 'suelo': d.suelo_banio})
    for d in Distribucion.objects.filter(banios=None).exclude(suelo_banio='').iterator():
        Banios.objects.update_or_create(inmueble_id=d.inmueble_id, defaults={'banios': 0, 'suelo': d.suelo_banio})


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0031_comprobaciones_de_datos'),
    ]

    operations = [
        migrations.RenameModel(old_name='Dormitorios', new_name='Distribucion'),
        migrations.AlterModelOptions(
            name='distribucion',
            options={'verbose_name': 'distribución', 'verbose_name_plural': 'distribución'},
        ),
        migrations.AlterField(model_name='distribucion', name='dobles', field=models.PositiveIntegerField(blank=True, null=True)),
        migrations.AlterField(model_name='distribucion', name='individuales', field=models.PositiveIntegerField(blank=True, null=True)),
        migrations.AlterField(
            model_name='distribucion', name='exteriores',
            field=models.PositiveIntegerField(blank=True, help_text='Cuántos de los dormitorios (dobles o individuales) dan al exterior. No suma al total.', null=True),
        ),
        migrations.AlterField(
            model_name='distribucion', name='suites',
            field=models.PositiveIntegerField(blank=True, help_text='Cuántos de los dormitorios (dobles o individuales) tienen baño propio. No suma al total.', null=True),
        ),
        migrations.AddField(model_name='distribucion', name='banios', field=models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField(
            model_name='distribucion', name='suelo_banio',
            field=models.CharField(blank=True, choices=[('parquet', 'Parquet'), ('tarima', 'Tarima'), ('gres', 'Gres'), ('baldosa', 'Baldosa'), ('terrazo', 'Terrazo'), ('marmol', 'Mármol'), ('microcemento', 'Microcemento'), ('hidraulico', 'Hidráulico'), ('otro', 'Otro')], default='', max_length=20),
        ),
        migrations.RunPython(banios_a_distribucion, distribucion_a_banios),
        migrations.DeleteModel(name='Banios'),
        migrations.RemoveConstraint(model_name='distribucion', name='dormitorios_suites_dentro_del_total'),
        migrations.RemoveConstraint(model_name='distribucion', name='dormitorios_exteriores_dentro_del_total'),
        migrations.AddConstraint(
            model_name='distribucion',
            constraint=models.CheckConstraint(
                condition=models.Q(suites__lte=models.F('dobles') + models.F('individuales')),
                name='dormitorios_suites_dentro_del_total',
                violation_error_message='Las suites no pueden superar el total de dormitorios.',
            ),
        ),
        migrations.AddConstraint(
            model_name='distribucion',
            constraint=models.CheckConstraint(
                condition=models.Q(exteriores__lte=models.F('dobles') + models.F('individuales')),
                name='dormitorios_exteriores_dentro_del_total',
                violation_error_message='Los dormitorios exteriores no pueden superar el total.',
            ),
        ),
    ]
