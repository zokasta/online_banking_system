# Generated by Django 5.0.7 on 2024-09-20 16:29

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bank', '0020_alter_creditcard_used'),
    ]

    operations = [
        migrations.AlterField(
            model_name='creditcard',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 20, 16, 29, 45, 308593, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 20, 16, 29, 45, 305025, tzinfo=datetime.timezone.utc)),
        ),
    ]
