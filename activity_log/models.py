# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.contrib import admin
from ntwf.models import WorkFlow as wf, Meta
from file_manager.models import Directory ,File
# Create your models here.
class Log(Meta):
    directory_id = models.ForeignKey(Directory, related_name="directory_id",on_delete=models.CASCADE,db_column="directory_id",db_constraint=False,null=True)
    file_id = models.ForeignKey(File, related_name="file_id",on_delete=models.CASCADE, db_column="file_id",blank=True,null=True,db_constraint=False)
    workflow_id = models.ForeignKey(wf, related_name="workflow_id", on_delete=models.CASCADE, db_column="workflow_id", null=True)
class Activity(Meta):
    name = models.CharField("Activity Name", max_length=256)
    message = models.CharField("Activity Message", max_length=512)
    #activity_time = models.(_(u"Activity Time"), blank=True)
    activity_time = models.DateTimeField(blank=True,null=True)
    log_id = models.ForeignKey(Log, related_name="related_activities", db_column="log_id",null=True,on_delete=models.CASCADE)
    user_id = models.ForeignKey(User,related_name="user_id",db_column="user_id",null=True,on_delete=models.CASCADE)
admin.site.register(Log)