# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User, Group


# Create your models here.
class Meta(models.Model):
    created_by_id = models.ForeignKey(
        User, on_delete=models.PROTECT,related_name="created%(app_label)s_%(class)s_related",db_column="created_by_id",default=1,null=True)
    modified_by_id = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,related_name="modified%(app_label)s_%(class)s_related", db_column="modified_by_id")
    created_date = models.DateTimeField("Created On", auto_now_add=True)
    modified_date = models.DateTimeField("Modified On", auto_now=True)
    class Meta:
        abstract = True

class State(Meta):
    
    name = models.CharField("State Name", max_length=256,unique=True)
    label = models.CharField("State Label", max_length=256)

    def __unicode__(self):
        return self.label

class WorkFlow(Meta):
    
    name = models.CharField("Name", max_length=256)

    # active_transition = models.ForeignKey(
    # Transition, on_delete=models.PROTECT, related_name="wf_trans",
    # db_column="active_transition")
    active_state = models.ForeignKey(
        State, on_delete=models.PROTECT, related_name="wf_state", null=True)
    is_template = models.BooleanField("Is Template",default=True)
    response_message = models.CharField("Response", max_length=512, null=True)
    # To integrate with other applications
    res_app = models.CharField("Application Name", max_length=256)
    res_model = models.CharField("Model Name", max_length=256)
    res_id = models.IntegerField("Record Id",null=True)
    chart_data = models.TextField("Chart Data",null=True)
    # To integrate with other applications END

    def __unicode__(self):
        return self.name

class Transition(Meta):
    name = models.CharField("Name", max_length=256)
    state_from_id = models.ForeignKey(
        State, on_delete=models.CASCADE, related_name="state_from",db_column="state_from_id")
    state_to_id = models.ForeignKey(
        State, on_delete=models.CASCADE, related_name="state_to",db_column="state_to_id")
    workflow_id = models.ForeignKey(WorkFlow, related_name="workflow_transition",
                                    on_delete=models.CASCADE, db_column="workflow_id", null=True)
    action = models.CharField("Action Type", choices=(
        ("backward", "Backward"), ("forward", "Forward")), max_length=16)
    is_initial = models.BooleanField("Initial State", default=False)
    is_final = models.BooleanField("Final State", default=False)
    auth_type = models.CharField("Auth Type", choices=(("template", "Template"),
                                                       ("user", "User"), ("group", "Group")), max_length=16)
    auth_user = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True if auth_type != "user" else False)
    auth_group = models.ForeignKey(
        Group, on_delete=models.PROTECT, null=True if auth_type != "group" else False)

    def __unicode__(self):
        return self.name




