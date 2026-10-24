import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0009_copiar_condiciones_e_historial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='condiciones',
            name='modalidad',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='condiciones', to='base.modalidad'),
        ),
        migrations.AlterField(
            model_name='historialprecio',
            name='modalidad',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='historial_precios', to='base.modalidad'),
        ),
        migrations.RemoveField(
            model_name='inmueble',
            name='condiciones',
        ),
        migrations.DeleteModel(
            name='CondicionesAlquiler',
        ),
        migrations.DeleteModel(
            name='HistorialRenta',
        ),
    ]
