# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-09 05:04
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('ntwf', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('file_manager', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True, verbose_name='Created On')),
                ('modified_date', models.DateTimeField(auto_now=True, verbose_name='Modified On')),
                ('name', models.CharField(max_length=256, verbose_name='Activity Name')),
                ('message', models.CharField(max_length=512, verbose_name='Activity Message')),
                ('activity_time', models.DateTimeField(blank=True, null=True)),
                ('created_by_id', models.ForeignKey(db_column='created_by_id', default=1, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='createdactivity_log_activity_related', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True, verbose_name='Created On')),
                ('modified_date', models.DateTimeField(auto_now=True, verbose_name='Modified On')),
                ('created_by_id', models.ForeignKey(db_column='created_by_id', default=1, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='createdactivity_log_log_related', to=settings.AUTH_USER_MODEL)),
                ('directory_id', models.ForeignKey(db_column='directory_id', db_constraint=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='directory_id', to='file_manager.Directory')),
                ('file_id', models.ForeignKey(blank=True, db_column='file_id', db_constraint=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='file_id', to='file_manager.File')),
                ('modified_by_id', models.ForeignKey(db_column='modified_by_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='modifiedactivity_log_log_related', to=settings.AUTH_USER_MODEL)),
                ('workflow_id', models.ForeignKey(db_column='workflow_id', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='workflow_id', to='ntwf.WorkFlow')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='activity',
            name='log_id',
            field=models.ForeignKey(db_column='log_id', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='related_activities', to='activity_log.Log'),
        ),
        migrations.AddField(
            model_name='activity',
            name='modified_by_id',
            field=models.ForeignKey(db_column='modified_by_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='modifiedactivity_log_activity_related', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='activity',
            name='user_id',
            field=models.ForeignKey(db_column='user_id', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_id', to=settings.AUTH_USER_MODEL),
        ),
    ]
