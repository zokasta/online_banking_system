# Generated by Django 5.0.7 on 2024-08-27 12:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bank', '0015_rename_state_id_city_state_rename_city_id_user_city'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='city',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bank.city'),
        ),
    ]
