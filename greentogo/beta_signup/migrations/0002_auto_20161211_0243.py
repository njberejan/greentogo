# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-11 02:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('beta_signup', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='customer',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='subscription',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='plan',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='stripe_id',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.DeleteModel(
            name='Plan',
        ),
    ]