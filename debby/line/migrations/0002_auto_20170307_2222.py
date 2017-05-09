# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-07 14:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('line', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='qamodel',
            old_name='keyword',
            new_name='phrase',
        ),
        migrations.RemoveField(
            model_name='qamodel',
            name='category',
        ),
        migrations.AddField(
            model_name='qamodel',
            name='callback',
            field=models.CharField(choices=[('BGRecord', '紀錄血糖'), ('FoodRecord', '紀錄飲食'), ('FoodQuery', '查詢食物熱量'), ('DrugQuery', '查詢藥物'), ('Chat', '閒聊')], default='Chat', max_length=20),
        ),
        migrations.AlterField(
            model_name='qamodel',
            name='answer',
            field=models.TextField(blank=True, max_length=200),
        ),
    ]
