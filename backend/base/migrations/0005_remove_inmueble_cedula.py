from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_cedula_a_registro_legal'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inmueble',
            name='cedula',
        ),
    ]
