# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-05-09 14:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Exercise',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=100)),
                ('start_from', models.DateTimeField()),
                ('duration', models.IntegerField()),
            ],
        ),
    ]
