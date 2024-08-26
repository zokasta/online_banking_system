# Generated by Django 5.0.7 on 2024-08-25 11:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bank', '0012_state_remove_account_deleted_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='city_id',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='bank.city'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user',
            name='gender',
            field=models.CharField(choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], default=1, max_length=10),
            preserve_default=False,
        ),
    ]
