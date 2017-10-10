# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
from django.db import models
from django.contrib.auth.models import User, Group
from django.contrib.postgres.fields import JSONField
from django.contrib import admin
from ntwf.models import WorkFlow as wf, Meta

# Create your models here.

class Tag(Meta):

    name = models.CharField("Tag Name", max_length=128)


class Directory(Meta):
    name = models.CharField("Directory Name", max_length=128)
    owner_id = models.ForeignKey(User, related_name="directory_owner", db_column="owner_id",)
    parent_id = models.ForeignKey(
        'self', null=True, related_name="sub_directories", db_column="parent_id",blank=True,on_delete=models.CASCADE)
    workflow_id = models.OneToOneField(wf, null=True, db_column="workflow_id",on_delete=models.PROTECT)
    tags = models.ManyToManyField(Tag, blank=True,null=True)
    # shared_ids = models.ManyToManyField(User, blank=True)


class File(Meta):
    name = models.CharField("File Name", max_length=256)
    modified_file_name=models.CharField("Modified_file_name",max_length=256, null=True)
    tags = models.ManyToManyField(Tag, blank=True,null=True,db_constraint=False)
    file_type = models.CharField("Type", max_length=128)
    file_content_type = models.CharField("Content Type", max_length=256,null=True)
    size = models.FloatField("Size", null=False)
    directory_id = models.ForeignKey(Directory, null=True, related_name="file_ids", db_column="directory_id",on_delete=models.CASCADE)
    owner_id = models.ForeignKey(User, related_name="file_owner", db_column="owner_id")
    workflow_id = models.OneToOneField(wf, null=True, related_name="workflow_ids",db_column="workflow_id",on_delete=models.PROTECT)
    # shared_ids = models.ManyToManyField(User, blank=True)



class Share(Meta):
    user_ids = models.ManyToManyField(User, blank=True )
    group_ids = models.ManyToManyField(Group, blank=True)
    directory_id = models.ForeignKey(
        Directory, null=True, related_name="shared_dirs", db_column="directory_id",on_delete=models.CASCADE,db_constraint=False)
    file_id = models.ForeignKey(
        File, null=True, related_name="shared_files", db_column="file_id",on_delete=models.CASCADE,db_constraint=False)
    can_read = models.NullBooleanField("Can Read")
    can_write = models.NullBooleanField("Can Write")
    can_delete = models.NullBooleanField("Can Delete")



