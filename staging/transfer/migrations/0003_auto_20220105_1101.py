# Generated by Django 3.0.4 on 2022-01-05 11:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transfer', '0002_auto_20220105_0753'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datatransfer',
            name='task_id',
            field=models.CharField(default='', max_length=100, null=True),
        ),
    ]
