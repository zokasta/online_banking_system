# Generated by Django 5.0.7 on 2024-08-08 05:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bank', '0004_user_reset_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='reset_token',
            field=models.TextField(null=True),
        ),
    ]
