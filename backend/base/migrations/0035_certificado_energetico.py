import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

LETRAS = 'ABCDEFG'


def a_certificados(apps, schema_editor):
    """One certificate per listing that had any of its data; `eficiencia` is the letter A-G, else empty.

    `nombre_eficiencia` held the same fact as `eficiencia`, so it is only a fallback for the letter.
    """
    Inmueble = apps.get_model('base', 'Inmueble')
    Certificado = apps.get_model('base', 'CertificadoEnergetico')
    Registro = apps.get_model('base', 'RegistroLegal')
    numeros = {r.inmueble_id: r.numero for r in Registro.objects.filter(tipo='certificado_energetico')}
    for i in Inmueble.objects.all():
        letra = next(
            (v.strip().upper() for v in (i.eficiencia, i.nombre_eficiencia) if v.strip().upper() in tuple(LETRAS)),
            '',
        )
        numero = numeros.get(i.pk, '')
        if letra or numero or i.consumo_energetico is not None or i.emisiones_co2 is not None:
            Certificado.objects.create(
                inmueble=i, numero=numero, eficiencia=letra,
                consumo_energetico=i.consumo_energetico, emisiones_co2=i.emisiones_co2,
            )
    Registro.objects.filter(tipo='certificado_energetico').delete()


def a_inmuebles(apps, schema_editor):
    Inmueble = apps.get_model('base', 'Inmueble')
    Certificado = apps.get_model('base', 'CertificadoEnergetico')
    Registro = apps.get_model('base', 'RegistroLegal')
    for c in Certificado.objects.all():
        Inmueble.objects.filter(pk=c.inmueble_id).update(
            eficiencia=c.eficiencia, nombre_eficiencia=c.eficiencia,
            consumo_energetico=c.consumo_energetico, emisiones_co2=c.emisiones_co2,
        )
        if c.numero:
            Registro.objects.create(inmueble_id=c.inmueble_id, tipo='certificado_energetico', numero=c.numero)


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0034_iva_derivado'),
    ]

    operations = [
        migrations.CreateModel(
            name='CertificadoEnergetico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(blank=True, default='', help_text='Número de registro del certificado; vacío si el anuncio no lo publica.', max_length=60)),
                ('eficiencia', models.CharField(blank=True, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E'), ('F', 'F'), ('G', 'G')], default='', max_length=1)),
                ('consumo_energetico', models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Consumo energético (kWh/m²/año)')),
                ('emisiones_co2', models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Emisiones (kg CO₂/m²/año)')),
                ('fecha_emision', models.DateField(blank=True, null=True)),
                ('fecha_vencimiento', models.DateField(blank=True, null=True)),
                ('inmueble', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='certificado_energetico', to='base.inmueble')),
            ],
            options={
                'verbose_name': 'certificado energético',
                'verbose_name_plural': 'certificados energéticos',
                'constraints': [
                    models.CheckConstraint(condition=models.Q(('consumo_energetico__isnull', True), ('consumo_energetico__gte', 0), _connector='OR'), name='certificado_consumo_no_negativo'),
                    models.CheckConstraint(condition=models.Q(('emisiones_co2__isnull', True), ('emisiones_co2__gte', 0), _connector='OR'), name='certificado_emisiones_no_negativas'),
                    models.CheckConstraint(condition=models.Q(('fecha_emision__isnull', True), ('fecha_vencimiento__isnull', True), ('fecha_vencimiento__gte', models.F('fecha_emision')), _connector='OR'), name='certificado_vencimiento_no_antes_de_emision', violation_error_message='El certificado no puede vencer antes de emitirse.'),
                ],
            },
        ),
        migrations.RunPython(a_certificados, a_inmuebles),
        migrations.RemoveConstraint(model_name='inmueble', name='inmueble_consumo_energetico_no_negativo'),
        migrations.RemoveConstraint(model_name='inmueble', name='inmueble_emisiones_co2_no_negativo'),
        migrations.RemoveField(model_name='inmueble', name='eficiencia'),
        migrations.RemoveField(model_name='inmueble', name='nombre_eficiencia'),
        migrations.RemoveField(model_name='inmueble', name='consumo_energetico'),
        migrations.RemoveField(model_name='inmueble', name='emisiones_co2'),
        migrations.AlterField(
            model_name='registrolegal',
            name='tipo',
            field=models.CharField(choices=[('aicat', 'Registro AICAT'), ('cedula_habitabilidad', 'Cédula de habitabilidad'), ('licencia_turistica', 'Licencia turística'), ('otro', 'Otro')], max_length=30),
        ),
    ]
