from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0014_matterport_a_media'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inmueble',
            name='matterport_url',
        ),
    ]
