# Generated by Django 5.0.7 on 2024-08-25 11:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bank', '0011_account_account_number_alter_account_debit_card'),
    ]

    operations = [
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.RemoveField(
            model_name='account',
            name='deleted_at',
        ),
        migrations.RemoveField(
            model_name='creditcard',
            name='deleted_at',
        ),
        migrations.RemoveField(
            model_name='report',
            name='deleted_at',
        ),
        migrations.RemoveField(
            model_name='transaction',
            name='deleted_at',
        ),
        migrations.RemoveField(
            model_name='user',
            name='deleted_at',
        ),
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('state_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bank.state')),
            ],
        ),
    ]
