# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-03 11:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FoodModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('calories', models.IntegerField(blank=True, null=True)),
                ('gi_value', models.IntegerField(blank=True, null=True)),
                ('food_name', models.CharField(max_length=50)),
                ('food_image_upload', models.ImageField(upload_to='FoodRecord')),
                ('note', models.CharField(max_length=200)),
                ('time', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]