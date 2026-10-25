from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0028_texto_libre_a_opciones'),
    ]

    operations = [
        migrations.RemoveField(model_name='otros', name='office'),
    ]
