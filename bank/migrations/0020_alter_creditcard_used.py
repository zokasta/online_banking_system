# Generated by Django 5.0.7 on 2024-09-20 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bank', '0019_creditcard_used'),
    ]

    operations = [
        migrations.AlterField(
            model_name='creditcard',
            name='used',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
