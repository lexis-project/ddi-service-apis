# Generated by Django 2.2.15 on 2022-01-14 16:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transfer', '0004_auto_20220105_1141'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datatransfer',
            name='created_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
