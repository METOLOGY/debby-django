# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-18 12:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ConsultFoodModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sample_name', models.CharField(max_length=100, unique=True, verbose_name='樣品名稱')),
                ('modified_calorie', models.FloatField(blank=True, null=True, verbose_name='修正熱量-成分值(kcal)')),
                ('carbohydrates', models.FloatField(blank=True, null=True, verbose_name='總碳水化合物-成分值(g)')),
                ('dietary_fiber', models.FloatField(blank=True, null=True, verbose_name='膳食纖維-成分值(g)')),
                ('metabolic_carbohydrates', models.FloatField(blank=True, null=True, verbose_name='可代謝醣量')),
                ('carbohydrates_equivalent', models.FloatField(blank=True, null=True, verbose_name='醣類份數當量')),
                ('white_rice_equivalent', models.FloatField(blank=True, null=True, verbose_name='幾碗白飯當量')),
            ],
        ),
    ]