# Generated by Django 5.0.7 on 2024-10-21 15:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bank', '0022_alter_creditcard_created_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='is_rolled_back',
            field=models.BooleanField(default=False),
        ),
    ]
