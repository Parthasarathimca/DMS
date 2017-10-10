# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime

from django.shortcuts import render
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
# from django.contrib.auth.models import User, Group
from rest_framework.viewsets import ModelViewSet

import config

import crud
from serializers import *

logger = logging.getLogger(__name__)
from activity_log.views import LogView
# Create your views here.

class WorkflowViewSet(ModelViewSet):
    table = WorkFlow._meta.db_table
    # queryset = WorkFlow.objects.raw("select * from {}".format(table))
    queryset = WorkFlow.objects.all()
    serializer_class = WorkflowSerializer

    # def create(self, request, *args, **kwargs):
    #     logger.debug("Workflow:: Create:: {}".format(request.data))

    def retrieve(self, request, pk=None):
        # workflow_obj = crud.get(self.table,crud.fetch_query(config.workflow,config.  ).format(pk))
        workflow_obj = crud.get(self.table, "*", "WHERE id={}".format(pk))
        logger.debug(
            "\n\nNTWF WF:Retrieve - Workflow Object {} ".format(workflow_obj))
        workflow_obj = workflow_obj and workflow_obj[0]
        transition_obj = crud.get(
            TransitionViewSet.table, "*", "WHERE workflow_id={}".format(pk))
        logger.debug(
            "\n\nNTWF WF:Retrieve - Transition Object {} ".format(transition_obj))
        workflow_obj.update({"workflow_transition": transition_obj})
        return Response(workflow_obj)
    
    def get_workflow_status(self,pk):
        workflow_obj = WorkFlow.objects.get(id=pk)
        transition_ids = WorkFlow.objects.get(
            id=pk).workflow_transition.filter(state_from_id=workflow_obj.active_state)
        response = {"active_state": {
            "id": workflow_obj.active_state.id,
            "label": workflow_obj.active_state.label
        },"workflow_id":pk,
            "urls": map( 
            lambda x: {"label": x.state_to_id.label, "action": x.action,
                       "url": str(pk) + "/update/" + str(x.state_to_id.id) + "/", x.auth_type: x.auth_user.id if x.auth_type == 'user' else x.auth_group.id}, transition_ids)}
        return response


    @detail_route(methods=["get"], url_path="status")
    def get_status(self, request, pk=None):
        response = self.get_workflow_status(pk)
        # possible_transition = trnansition_ids.get(state_from_id=status.get('active_state'),state_to_id=status.get('active_state'))
        # print "POssible Transition",possible_transition
        return Response(response)
    @detail_route(methods=["put"], url_path="update/(?P<state_id>[0-9]+)")
    def update_status(self, request, pk=None, state_id=None):
        user_name = request.user.first_name + request.user.last_name
        user = User.objects.get(id=request.user.id)
        logger.debug("Data {} {} ".format(user.__dict__, user.groups))
        payload = request.data
        logger.debug("Payload {} {} ".format(pk, state_id))
        workflow_obj = WorkFlow.objects.get(id=pk)
        stage_from = workflow_obj.active_state
        target_transient = workflow_obj.workflow_transition.get(
            state_from_id=workflow_obj.active_state.id, state_to_id=state_id)
        if target_transient.auth_user is None:
            workflow_obj.active_state = State.objects.get(id=state_id)
            workflow_obj.save()
            return Response({"status": "updated"})
        elif target_transient.auth_user.id == user.id:
            workflow_obj.active_state = State.objects.get(id=state_id)
            stage_to = workflow_obj.active_state
            workflow_obj.save()
            # Activity log
            param = {'field': 'workflow_id', 'label': 'Workflow',
                     'user_name': user_name, 'workflow_id': workflow_obj.id}
            fields = [] 
            fields.append(stage_from)
            fields.append(stage_to)
            log_view = LogView()
            request_data = {}
            request_data = request.data
            request_data.update({"user_id": request.user.id})
            log_view.generate_log(request_data, param, "", fields)
            return Response({"status": "updated"})
        else:
            return Response({"status": "Invalid User/You are not auth to use it"})
        return Response("N/A")

    @detail_route(methods=["put"], url_path="clone")
    def clone_wf(self, request, pk=None):
        user_name = request.user.first_name + request.user.last_name
        custom_name = request.data.get('name')
        workflow_obj = WorkFlow.objects.get(pk=pk)
        workflow_transition = Transition.objects.values("name", "action", "is_initial", "is_final", "auth_type",
                                                        "state_from_id", "state_to_id", "auth_user", "auth_group").filter(workflow_id_id=pk)
        workflow_obj.id = None
        workflow_obj.pk = None
        workflow_obj.is_template = False
        workflow_obj.name = workflow_obj.name + ' - ' + custom_name
        workflow_obj.save()
        for item in workflow_transition:
            item.update({"workflow_id": workflow_obj.id, "created_by": 1})
            t = TransitionSerializer(data=item)
            if t.is_valid():
                t.save()
            else:
                logger.info("Error: " + t.errors)
        request_data = request.data
        request_data.update(
            {"id": workflow_obj.id, 'user_id': request.user.id})
        param = {'field': 'workflow_id',
                 'label': 'Workflow', 'user_name': user_name}
        log_view = LogView()
        log_view.generate_log(request_data, param)
        return Response(workflow_obj.id)

    @list_route(methods=["get"], url_path="templates")
    def get_templates(self, request, *args, **kwargs):
        template_res = crud.get(self.table, "*", "WHERE is_template IS true")
        return Response(template_res)
    
   


class TransitionViewSet(ModelViewSet):
    table = Transition._meta.db_table
    queryset = Transition.objects.all()
    serializer_class = TransitionSerializer


class StateViewSet(ModelViewSet):
    table = State._meta.db_table
    queryset = State.objects.raw("select * from {}".format(table))
    serializer_class = StateSerializer

    def create(self, request):
        state_res = request.data
        state_res.update({'name': state_res.get(
            'label').replace(' ', '_').lower()})
        serializer = self.serializer_class(data=state_res)
        if serializer.is_valid():
            state_res.update({'created_date': datetime.now(), 'modified_date': datetime.now(
            ), 'created_by_id': request.user.id, 'modified_by_id': request.user.id})
            state_id = crud.add(self.table, state_res)
            return Response(state_id)
        else:
            return Response(serializer.errors)
class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
