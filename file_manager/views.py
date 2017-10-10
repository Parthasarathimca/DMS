# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,  unicode_literals)
import os
import shutil
import time
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.shortcuts import render
from django.conf import settings
from .models import *
from .serializers import *
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import crud
import logging
import json
import re
import base64
from PyPDF2 import PdfFileMerger
import pdfkit
from docx2html import convert
# from django.db import connection
# from subprocess import call
from jenkinsapi.jenkins import Jenkins
from ntwf.views import WorkflowViewSet
from datetime import datetime
from file_manager.models import Directory
from activity_log.models import Log, Activity
from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser
from activity_log.views import LogView
from wsgiref.util import FileWrapper
from django.http import HttpResponse
from beefish import encrypt_file, decrypt_file
from . import config as c
from UAM.uam_session_sync import uam_sessions_sync
from pprint import pprint
from elasticsearch import Elasticsearch



connection_es=Elasticsearch()

logger = logging.getLogger(__name__)
obj = WorkflowViewSet()
# Login Response Function Using JWT


try:
    jenkins_url = "http://192.168.10.71:8080"
    server = Jenkins(jenkins_url, username='transform',password='transform123')
    job_instance = server.get_job('DMS-Transform-WS-Test')
    running = job_instance.is_queued_or_running()
    latestBuild = job_instance.get_last_build()
    build_number = str(latestBuild).split('#')
except Exception as a:
    build_number = [5, 6]

def jwt_response_payload_handler(token, user=None, request=None):
    request.user = user
    uam_sessions_sync(request, c.strUAMLink, c.strAppName, c.strAppClient,
                      "login", token, request.META.get('HTTP_X_FORWARDED_FOR'))
    try:
        jenkins_url = "http://192.168.10.71:8080"
        server = Jenkins(jenkins_url, username='transform',
                         password='transform123')
        job_instance = server.get_job('DMS-Transform-WS-Test')
        running = job_instance.is_queued_or_running()
        latestBuild = job_instance.get_last_build()
        build_number = str(latestBuild).split('#')
        build_date = job_instance.get_build_metadata(
            int(build_number and build_number[1])).get_timestamp().strftime('%d-%b-%y')
    except Exception as a:
        logger.info("exception", a)
        build_number = [5, "N/A"]
        build_date = "N/A"
    return {
        'token': token,
        'user': UserSerializer(user, context={'request': request}).data,
        'build_info': {"number": build_number[1], "date": build_date}

    }

# Create your views here.


class UserView(ModelViewSet):
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer
    table = User._meta.db_table


class DirectoryView(ModelViewSet):
    """
    create:
    Creates a new Directory.
    \nSend payload based on Example value
    get_child_dirs:
    <b>Filter parent directory\n
    To filter child directories of respective parent directories by taking directory id as input
    """
    queryset = Directory.objects.all().order_by(c.name)
    serializer_class = DirectorySerializer
    table = Directory._meta.db_table
    track_fields = {c.name: {c.field: c.name, c.label: "Name"},
                    c.workflow_id: {c.field: c.workflow_id, c.label: "Workflow"}}

    def get_queryset(self):
        """ 
        This view should return a list of all the Directories
        for the currently authenticated user.
        """
        user = self.request.user
        return Directory.objects.filter(owner_id=user.id)

# custom  create method
    def create(self, request):
        """
        <b>Author: </b> Manickam \n
        Service to create a new Directory. Send payload based on Example value.
        \n
        """
        try:
            uam_func_sync(request, c.strUAMLink, c.strAppName, c.strAppClient,
                          "File Manager ", "Create", request.session.session_key, request.META.get('HTTP_X_FORWARDED_FOR'))
        except Exception as e:
            logger.info(e)
        user_name = request.user.first_name + request.user.last_name
        user_id = request.user.id
        # directory_data = request.data
        # tags = directory_data.pop(c.tags)
        # response = crud.add(self.table, directory_data)

        # return Response(response)
        serializer = DirectorySerializer(data=request.data)
        if serializer.is_valid():
            directory_data = request.data
            tag = [istags for istags in directory_data.keys() if istags ==
                   c.tags]
            if istags:
                tags = directory_data.pop("tags")
            directory_data.update({'created_date': datetime.now(), 'modified_date': datetime.now(
            ), 'created_by_id': directory_data.get('owner_id'), 'modified_by_id': directory_data.get('owner_id')})
            #tags = directory_data.pop(c.tags)
            # directory_data.update({c.created_date:datetime.now(),c.modified_date:datetime.now(),c.created_by_id:directory_data.get(c.owner_id),c.modified_by_id:directory_data.get(c.owner_id)})
            directory_id = crud.add(self.table, directory_data)
            if tags:
                for tag in tags:
                    directory_tag_data = {
                        c.directory_id: directory_id, c.tag_id: tag}
                    crud.add(c.tag_dir_rel,directory_tag_data)
            param = {'field': 'directory_id',
                     'label': 'Directory', 'user_name': user_name}
            # self.add_log(act_log_data=serializer.data)
            act_log_data = request.data
            act_log_data.update({'id': directory_id, 'user_id': user_id})
            log_view = LogView()
            log_view.generate_log(act_log_data, param)
            # return Response(directory_id)
            # act_log_data=request.data
            # act_log_data.update({'id':directory_id})
            # log_view = LogView()
            # log_view.generate_log(act_log_data,param)e

            response = crud.get(self.table, c.all,
                                c.where_id_param.format(directory_id))
            return Response(response[0])
        else:
            return Response(serializer.errors)

    def tag_change(self, pk, requst_data, key):
        
        tags = crud.execute("select name, file_manager_tag.id from file_manager_tag inner join file_manager_" + key +
                            "_tags on file_manager_tag.id=file_manager_" + str(key) + "_tags.tag_id where " + key + "_id={}".format(pk))
        old_tag = []
        new_tag = []
        new_tag_ids = {}
        old_tag_ids = {}
        if tags:
            for tag in tags:
                old_tag_ids.update({str(tag[0]): tag[1]})
                old_tag.append(str(tag[0]))
        else:
            old_tag = []
        directory_update = requst_data
        new_tags = directory_update.get('tags')
        newTags = ""
        directory_update = requst_data
        new_tags = directory_update.get(c.tags)
        newTags = ""
        if new_tags:
            new_tags = tuple(new_tags)
            if len(new_tags) > 1:
                newTags = crud.get("file_manager_tag", [
                                   'id,name'], 'where id in ' + str(new_tags))
            elif len(new_tags) == 1:
                newTags = crud.get("file_manager_tag", [
                                   'id,name'], 'where id = ' + str(new_tags[0]))
        if newTags:
            for nt in newTags:
                new_tag_ids.update({str(nt.get(c.name)): nt.get('id')})
                new_tag.append(str(nt.get(c.name)))
        # else:

        def lr_diff(l, r): return list(set(l).difference(r))
        deleted_tag = lr_diff(old_tag, new_tag)
        added_tag = set(new_tag).difference(old_tag)
        tag_details = {}
        tag_details['added_tag'] = added_tag
        tag_details['deleted_tag'] = deleted_tag
        tag_details['new_tag_ids'] = new_tag_ids
        tag_details['old_tag_ids'] = old_tag_ids
        tag_details['new_tag'] = new_tag
        return tag_details

    def update(self, request, pk=None):


        
        try:
            uam_func_sync(request, c.strUAMLink, c.strAppName, c.strAppClient,
                          "File Manager ", "Update", request.session.session_key, request.META.get('HTTP_X_FORWARDED_FOR'))
        except Exception as e:
            logger.info(e)
        user_name = request.user.first_name + request.user.last_name
        try:
            # request = dict(request.data)
            param = {'field': 'directory_id','label': 'Directory', 'user_name': user_name}
            # print "\n\n\n@@@@@@data @@",request.data
            # payload = request.data
            # #payload=serializer.data
            # print "original data:%%%%%%%%,",payload
            original_data = crud.get(
                self.table, c.all, 'where id=' + str(pk))[0]
            # tags = crud.execute("select tag_id from file_manager_directory_tags where directory_id={}".format(pk))
            # shared_ids = crud.execute("select id from file_manager_share where directory_id={}".format(pk))
            # original_data.update({c.tags:list(tags and zip(*tags)[0]),    'shared_ids':list(shared_ids and zip(*shared_ids)[0])})
            # logger.debug("Files:: get_parent_dirs: Parent Files{}".format(original_data))

            # #try:
            # payload.update({"id":pk})
            # tags = payload.pop(c.tags)
            # file_ids=payload.pop("file_ids")
            # parent_id=payload.pop("parent_id")
            # shared_ids = payload.pop("shared_ids")
            # sub_directories=payload.pop("sub_directories")
            # workflow_id=payload.pop(c.workflow_id)
            # response = crud.update(self.table,payload )
            # print "Response",response
            param = {'field': 'directory_id',
                     'label': 'Directory', 'user_name': user_name}
            original_data = crud.get(
                self.table, c.all, 'where id=' + str(pk))[0]
            dir_obj = Directory.objects.get(id=pk)
            serializer = DirectorySerializer(dir_obj, data=request.data)
            if serializer.is_valid():
                
                tag_details=self.tag_change(pk,request.data,"directory")
                new_tag_ids={}
                old_tag_ids={} 
                added_tag=tag_details.get("added_tag")
                deleted_tag=tag_details.get("deleted_tag")
                new_tag_ids.update(tag_details.get("new_tag_ids"))
                old_tag_ids.update(tag_details.get("old_tag_ids"))
                directory_update = request.data
                for i in directory_update.keys():
                    if i in [c.tags, 'parent_id', 'workflow_id', 'shared_dirs', 'file_ids', 'sub_directories']:
                        if i == c.tags:
                            update_tag = directory_update.pop(i)
                        else:
                            directory_update.pop(i)
                directory_id = crud.update(self.table, directory_update)
                if added_tag:
                    for tag in added_tag:
                        directory_tag_data = {
                            c.directory_id: directory_id, "tag_id": new_tag_ids.get(tag)}
                        crud.add(c.tag_dir_rel, directory_tag_data)
                if deleted_tag:
                    for tag in deleted_tag:
                        try:
                            crud.execute("delete from  file_manager_directory_tags where tag_id={} and directory_id={}".format(
                                old_tag_ids.get(tag), pk), True)
                        except Exception as err:
                            return Response(err)
                logger.debug("Files:: Serializer{}".format(request.data))
                log_view = LogView()
                original_data1 = {}
                map(lambda x: original_data1.update(
                    {str(x): original_data.get(x)}), original_data)
                # original_data1.update({c.tags:old_tag})
                current_data = request.data
                current_data.update({'user_id': request.user.id})
                ChangeTag = {}
                if added_tag:
                    ChangeTag.update({"Added": {c.field: "Tag", "tag": [
                                     Tag for Tag in added_tag], "action": "Added"}})
                if deleted_tag:
                    ChangeTag.update({"Removed":{c.field:"Tag","tag":[Tag for Tag in deleted_tag],"action":"Removed"}})
                log_view.generate_log(current_data,param,original_data1,self.track_fields,ChangeTag,)
                return Response(crud.get(self.table,c.all,c.where_id_param.format(directory_id)))
            else:
                logger.debug("Files:: Serializer{}".format(serializer.errors))
                return Response(serializer.errors)
        except Exception as err:
            return Response(err)

    def list(self, request, *args, **kwargs):
        """Overridden GET For Directory Informations Created by a Particular Owner """
        try:
            l = {}
            response = request.user.id
            directory_info = crud.get(
                self.table, "*", "where owner_id = " + str(response))
            sub_directories = map(lambda i: i.update({'sub_directories': crud.get(self.table, "*", "where parent_id=" + str(
                i['id'])), 'file_ids': crud.get(FileView.table, "*", "where directory_id=" + str(i['id']))}), directory_info)
            return Response(directory_info)
        except Exception as e:
            return Response(e)

    def retrieve(self, request, pk=None, *args, **kwargs):
        """Overridden GET For Particular Directory Informations about Shared & its Tags"""
        try:
            file_view_object = FileView()
            directory_request = pk
            directory_info = crud.get(
                self.table, "*", "where id = %s" % (directory_request))
            directory_info = directory_info and directory_info[0]
            shared_info = crud.get(
                ShareView.table, "*", "where directory_id = %s " % (directory_request))
            tag_info = crud.execute(
                "select tag_id from  file_manager_directory_tags where directory_id = %s " % (directory_request))
            tag_info = zip(*tag_info)[0] if tag_info and tag_info[0] else []
            file_info = crud.get(
                FileView.table, "*", "where directory_id = {0}".format(directory_request))
            file_data = file_view_object.get_file_data(request, file_info)
            sub_directories = crud.get(
                self.table, "*", "where parent_id=" + str(directory_info['id']))
            if directory_info:
                directory_info.update({"shared_dirs": shared_info, "tags": tag_info,
                                       "file_ids": file_data, "sub_directories": sub_directories})
            return Response(directory_info)
        except Exception as e:
            return Response(e)

    # Takes directory ID as input and returns its child directories
    @detail_route(methods=["get"], url_path="child-dirs")
    def get_child_dirs(self, request, pk=None, *args, **kwargs):
        file_view_object = FileView()
        # child_object = crud.get(self.table,c.all,"where
        # parent_id={}".format(pk))
        # child_object = Directory.objects.filter(parent_id=pk,owner_id=request.user.id).order_by(c.name)
        files = crud.get('file_manager_file', "*",
                         "where directory_id ={0} and owner_id = {1}" .format(int(pk), request.user.id))
        child_object = crud.get(
            self.table, "*", "where parent_id={0} and owner_id={1} order by name".format(int(pk), request.user.id))
        child_dirs = map(lambda i: i.update({'file_ids': file_view_object.get_file_data(request, files), 'shared_dirs': self.get_directory_data(request, int(pk)), 'sub_directories': [
                         item for sublist in crud.execute("select id from file_manager_directory where parent_id = {0}".format(i['id'])) for item in sublist]}), child_object)
        logger.debug(
            "Dictionary:: get_child_dirs: Child Object {} ".format(child_object))
        # child_dirs = DirectorySerializer(child_object, many=True)
        # logger.debug(
        #     "Dictionary:: get_child_dirs: Child DIrs{}".format(child_dirs))

        return Response(child_object)

    @list_route(methods=["get"], url_path="parent-dirs")
    def get_parent_dirs(self, request, *args, **kwargs):
        try:
            response = crud.get(
                self.table, c.all, "where owner_id={} and parent_id is null order by name".format(request.user.id))
            sub_directories = map(lambda i: i.update({'sub_directories': crud.get(self.table, "*", "where parent_id=" + str(
                i['id'])), 'file_ids': crud.get(FileView.table, "*", "where directory_id=" + str(i['id']))}), response)
            logger.debug(
                "Files:: get_parent_dirs: Parent Files{}".format(response))
            return Response(response)
        except Exception as e:
            return Response({"error": e})

    @list_route(methods=["get"], url_path="shared-dirs")
    def get_shared_dirs(self, request, *args, **kwargs):
        """Provide Response about Shared Directories for a particular User and the Group"""
        user_id = request.user.id
        try:
            dirs = crud.execute("""select s.directory_id,u.user_id,g.group_id from file_manager_share as s 
            inner join file_manager_share_user_ids as u on  (s.id = u.share_id and u.user_id = {0}) and directory_id is not null
            inner join auth_user_groups as ag on ag.user_id = {0}
            left join file_manager_share_group_ids as g on g.group_id= ag.group_id and s.id = g.share_id """.format(user_id))
            dirs = zip(*dirs)[0] if dirs and dirs[0] else False
            logger.info("dirs======================>", dirs)
            if dirs is not False:
                dir_object = Directory.objects.filter(
                    id__in=dirs).order_by(c.name)
                shared = DirectorySerializer(dir_object, many=True)
                return Response(shared.data)
            else:
                return Response({"status": "No Directories"})
        except Exception as e:
            return Response({"error": e})

    @detail_route(methods=[c.put], url_path=c.share)
    def share_dir(self, request, pk=None, *args, **kwargs):
        track_fields = {c.can_read: c.read,
                        c.can_write: c.write, c.can_delete: c.delete}
        log_view = LogView()
        share_res = request.data
        share_res.update({c.directory_id: int(pk)})
        share = ShareSerializer(data=share_res)

        if share.is_valid():
            share.save()
            param={c.field:c.directory_id,c.label:c.directory,c.action:c.share}
            request_data=share.data
            request_data.update({c.user_id:request.user.id})
            log_view.generate_log(request_data,param,"",track_fields,"")
            
            return Response(share.data)
        else:
            return Response(share.errors)

    def get_directory_data(self, request, parent_id='null'):
        l = {}
        directories = crud.get(
            self.table, "*", "where parent_id = {0} and owner_id = {1}" .format(parent_id, request.user.id))
        crud.execute("create or replace view directory_share as select ds.id,ds.directory_id,dsu.user_id,dsg.group_id,ds.can_read,ds.can_write,ds.can_delete from file_manager_share as ds left join file_manager_share_group_ids as dsg on ds.id = dsg.share_id left join file_manager_share_user_ids as dsu on ds.id = dsu.share_id where directory_id is not null")
        directory_share_data = crud.get('directory_share', "*", '')
        map(lambda x: l.get(x.get('directory_id')).get('shared_ids').append(x) if x.get('directory_id')
            in l else l.update({x.get('directory_id'): {'shared_ids': [x]}}), directory_share_data)
        map(lambda (k, v): v.update({'user_ids': list(set(map(lambda fd: fd.get('user_id'), v.get('shared_ids')))), 'group_ids': list(
            set(map(lambda fd: fd.get('group_id'), v.get('shared_ids'))))}), l.iteritems())
        tags = map(lambda f: f.update({'tags': [i[0] for i in crud.execute("select tag_id from {0} where directory_id = {1}".format(
            "file_manager_directory_tags", f.get('id')))]}) if f.get('id') else '', directories)
        shared_dirs = map(lambda f: f.update(
            {'shared_dirs': [l.get(f.get('id'))]}), directories)
        return directories


class FileView(ModelViewSet):
    """
    upload_file:
    Send file as multipart form data , set file_key as file and send directory_id
    Ex:
    {"file":file,
    "directory_id":number
    }
    """
    queryset = File.objects.all().order_by('name')
    serializer_class = FileSerializer
    table = File._meta.db_table

    @list_route(methods=["post"], url_path="upload")
    def upload_file(self, request, *args, **kwargs):
        
        file = request.data.get('file')
        if request.data.get('directory_id') != 'null':
            modified_file_name = map(lambda x: x.replace("\'", "").strip() if x.find("'") != -1 else x.replace(' ', '_').strip(), file.name.split(
                '.')); modified_file_name[-1]='.' + modified_file_name[-1]; modified_file_name.insert(-2, request.data.get('directory_id'))
        else:
            modified_file_name = map(lambda x: x.replace("\'", "").strip() if x.find("'") != -1 else x.replace(
                ' ', '_').strip(), file.name.split('.')); modified_file_name[-1]='.' + modified_file_name[-1]
        try:
            if not os.path.isdir(settings.MEDIA_ROOT + str(request.user.id)):
                os.mkdir(settings.MEDIA_ROOT + str(request.user.id))
            upload_dir = default_storage.save(
                ''.join(modified_file_name), ContentFile(file.read()))
            user_name = request.user.first_name + request.user.last_name
            user_id = request.user.id
            tmp_file = os.path.join(settings.MEDIA_ROOT, upload_dir)
            encrypt_file(os.path.join(settings.MEDIA_ROOT, upload_dir), os.path.join(
                settings.MEDIA_ROOT + str(request.user.id), base64.b16encode(upload_dir)), '123')
            os.remove(tmp_file)
            file_data = {c.name: file.name, "modified_file_name": ''.join(modified_file_name), "file_type": file.name.split(
                '.')[-1] or 'n/a', "size": file.size, "file_content_type": file.content_type,
                "created_by_id": request.user.id, "owner_id": request.user.id, "created_date": datetime.now(),
                "modified_date": datetime.now()}
            connection_es.index(index='dms_test',doc_type='post',body={'name':file.name,'type':'File','content_type':file.content_type,'owner_id':request.user.id})
            if request.data.get('directory_id') != 'null':
                file_data.update(
                    {c.directory_id: request.data.get('directory_id')})
            param = {'field': 'file_id',
                     'label': 'File', 'user_name': user_name}
            act_log_data = file_data
            response = crud.add(self.table, file_data)
            file_data.update({"id": response})
            act_log_data.update({'user_id': user_id})
            log_view = LogView()
            log_view.generate_log(act_log_data, param)
            return Response(response)
        except Exception as e:
            return Response({"error": e})

# update file override
    def update(self, request, pk=None):
        user_name = request.user.first_name + request.user.last_name
        track_fields = {c.name: {c.field: c.name, c.label: "Name"},
                        c.tags: {c.field: c.tags, c.label: "Tags"}}
        param = {'field': 'file_id', 'label': 'File', 'user_name': user_name}
        original_data = crud.get(self.table, c.all, 'where id=' + pk)[0]
        logger.debug(
            "Files:: get_parent_dirs: Parent Files{}".format(original_data))
        dir_obj = File.objects.get(id=pk)
        serializer = FileSerializer(dir_obj, data=request.data)
        if serializer.is_valid():
            dir_view = DirectoryView()
            tag_details = dir_view.tag_change(pk, request.data, "file")
            new_tag_ids = {}
            old_tag_ids = {}
            added_tag = tag_details.get("added_tag")
            new_tag = tag_details.get("new_tag")
            deleted_tag = tag_details.get("deleted_tag")
            new_tag_ids.update(tag_details.get("new_tag_ids"))
            old_tag_ids.update(tag_details.get("old_tag_ids"))
            file_update = request.data
            update_tag = file_update.pop(c.tags)
            serializer.save()
            file_id = pk
            # if added_tag:
            #     for tag in added_tag:
            #         file_tag_data = {"file_id": file_id,
            #                          "tag_id": new_tag_ids.get(tag)}
            #         crud.add('file_manager_file_tags', file_tag_data)
            if deleted_tag:
                for tag in deleted_tag:
                    try:
                        crud.execute("delete from  file_manager_file_tags where tag_id={} and file_id={}".format(
                            old_tag_ids.get(tag), pk), True)
                    except Exception as err:
                        return Response(err)
            log_view = LogView()
            original_data1 = {}
            map(lambda x: original_data1.update(
                {str(x): original_data.get(x)}), original_data)
            ChangeTag = {}
            if added_tag:
                ChangeTag.update({"Added": {c.field: "Tag", "tag": [
                                 Tag for Tag in added_tag], "action": "Added"}})
            if deleted_tag:
                ChangeTag.update({"Removed":{c.field:"Tag","tag":[Tag for Tag in deleted_tag],"action":"Removed"}})
            request_data=request.data
            request_data.update({'user_id':request.user.id})
            log_view.generate_log(request.data,param,original_data1,track_fields,ChangeTag)
            # settings.connection_es.update(index='dms_test',doc_type='post',body={'doc':{'name':file.name,'type':'File','content_type':file.content_type,'owner_id':request.user.id,'tags':''}})
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    def destroy(self, request, pk=None):
        try:
            deletedFileName = crud.execute(
                "delete from {0} where id = {1} RETURNING name".format("file_manager_file", int(pk)))
            deletedFileName = zip(
                *deletedFileName)[0] if deletedFileName and deletedFileName[0] else False
            file_path = os.path.join(
                settings.MEDIA_ROOT, str(deletedFileName[0]))
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                return Response({"error": e})
            return Response({"Deleted": "File Removed"})
        except Exception as e:
            return Response({"error": e})

    def get_file_data(self, request, files):
        l = {}
        crud.execute("create or replace view file_share as select fs.id,fs.file_id,fsu.user_id,fsg.group_id,fs.can_read,fs.can_write,fs.can_delete from file_manager_share as fs left join file_manager_share_group_ids as fsg on fs.id = fsg.share_id left join file_manager_share_user_ids as fsu on fs.id = fsu.share_id where file_id is not null")
        file_share_data = crud.get('file_share', "*", '')
        map(lambda x: l.get(x.get('file_id')).get('shared_ids').append(x) if x.get(
            'file_id') in l else l.update({x.get('file_id'): {'shared_ids': [x]}}), file_share_data)
        map(lambda (k, v): v.update({'user_ids': list(set(map(lambda fd: fd.get('user_id'), v.get('shared_ids')))), 'group_ids': list(
            set(map(lambda fd: fd.get('group_id'), v.get('shared_ids'))))}), l.iteritems())
        tags = map(lambda f: f.update({'tags': [i[0] for i in crud.execute("select tag_id from {0} where file_id = {1}".format(
            "file_manager_file_tags", f.get('id')))]}) if f.get('id') else '', files)
        workflow_info = map(lambda i: i.update({'workflow_id': obj.get_workflow_status(
            i['workflow_id'])}) if i.get('workflow_id') else '', files)
        shared_files = map(lambda f: f.update(
            {'shared_files': l.get(f.get('id'))}), files)
        return files

    @list_route(methods=["get"], url_path="parent-files")
    def get_parent_files(self, request, *args, **kwargs):
        try:
            files = crud.get(
                self.table, "*", "where directory_id is null and owner_id = {0} order by created_date desc" .format(request.user.id))
            shared_files = self.get_file_data(request, files)
            logger.debug(
                "Files:: get_parent_files: Parent Files{}".format(shared_files))
            return Response(shared_files)
        except Exception as e:
            return Response({"error": e})

    @list_route(methods=["get"], url_path="shared-files")
    def get_shared_files(self, request, *args, **kwargs):
        """Provide Response about Shared Files for a particular User and the Group """
        user_id = request.user.id
        try:
            files = crud.execute("""select fs.file_id,fu.user_id,fg.group_id from file_manager_share as fs 
                    inner join file_manager_share_user_ids as fu on (fs.id = fu.share_id and fu.user_id = {0}) and file_id is not null
                    inner join auth_user_groups as fag on fag.user_id = {0}
                    left join file_manager_share_group_ids as fg on fg.group_id = fag.group_id and fs.id = fg.share_id """ .format(user_id))
            files = zip(*files)[0] if files and files[0] else False
            if files is not False:
                file_object = File.objects.filter(
                    id__in=files).order_by(c.name)
                shared = FileSerializer(file_object, many=True)
                return Response(shared.data)
            else:
                return Response({"status": "No Files"})
        except Exception as e:
            return Response({"error": e})
    #@detail_route(methods=["get"], url_path="download",permission_classes=(AllowAny,))

    @detail_route(methods=[c.put], url_path=c.share)
    def share_file(self, request, pk=None, *args, **kwargs):
        share_res = request.data
        track_fields = {c.can_read: c.read,
                        c.can_write: c.write, c.can_delete: c.delete}
        log_view = LogView()
        share_res.update({c.file_id: int(pk)})
        share = ShareSerializer(data=share_res)
        if share.is_valid():
            share.save()
            param = {c.field: c.file_id,
                     c.label: c.file_key, c.action: c.share}
            request_data = share.data
            request_data.update({c.user_id: request.user.id})
            log_view.generate_log(request_data, param, "", track_fields, "")
        else:
            return Response(c.share_invalid)
        return Response(share.data)

    @detail_route(methods=["get"], url_path="download", permission_classes=(AllowAny,))
    def download(self, request, pk=None, *args):
        file_res = File.objects.get(id=pk)
        decrypt_file(os.path.join(settings.MEDIA_ROOT + str(crud.get(self.table, "*", 'where id=' + pk)[0].get(
            'owner_id')) + '/' + base64.b16encode(file_res.name)), os.path.join(settings.MEDIA_ROOT + file_res.name), '123')
        file = open(settings.MEDIA_ROOT + file_res.name, 'rb')
        response = HttpResponse(FileWrapper(
            file), content_type=file_res.file_content_type)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(
            file_res.name)
        os.remove(os.path.join(settings.MEDIA_ROOT + file_res.name))
        return response
    # docx to html (i.e only for docx trying for solution to open odt,doc)
    @detail_route(methods=['get'], url_path='edit')
    def edit_file(self, request, pk=None):
        file_res = File.objects.get(id=pk)
        decrypt_file(os.path.join(settings.MEDIA_ROOT+str(crud.get(self.table,"*",'where id='+pk)[0].get('owner_id'))+'/'+base64.b16encode(file_res.modified_file_name)),os.path.join(settings.MEDIA_ROOT+file_res.modified_file_name),'123')
        os.chdir(settings.MEDIA_ROOT)
        os.system('unoconv --format=xhtml '+settings.MEDIA_ROOT+FileSerializer(File.objects.get(id=pk)).data.get('modified_file_name'))
        os.remove(os.path.join(settings.MEDIA_ROOT+file_res.modified_file_name))
        return Response({'contents':data_edit})
    # pdf merger
    @detail_route(methods=['get'], url_path='edit_pdfconvert')
    def pdf_merger(self, requets, pk=None):
        merger = PdfFileMerger()
        map(lambda x: merger.append(FileSerializer(x).data.get(c.name)),
            File.objects.filter(id__in=re.findall(r'(\d+)', str(pk))))
        merger.write('/home/next/Downloads/hj.pdf')
        return HttpResponse('Done')
    # save module for editor
    @detail_route(methods=['put'], url_path='save')
    def save_editor(self, request, pk=None, *args, **kwargs):
        file_res = File.objects.get(id=pk)
        decrypt_file(os.path.join(settings.MEDIA_ROOT + str(crud.get(self.table, "*", 'where id=' + pk)[0].get('owner_id')) + '/' + base64.b16encode(
            file_res.modified_file_name)), os.path.join(settings.MEDIA_ROOT + file_res.modified_file_name), '123')
        self.org_data = convert(settings.MEDIA_ROOT + FileSerializer(
            File.objects.get(id=pk)).data.get('modified_file_name'))
        os.remove(os.path.join(settings.MEDIA_ROOT +
                               file_res.modified_file_name))
        if self.org_data != request.data:
            # Activity log
            request_data = {}
            param = {'field': 'file_id', 'file_id': pk, 'label': 'version'}
            track_fields = {c.can_read: c.read,
                            c.can_write: c.write, c.can_delete: c.delete}
            request_data.update({'user_id': request.user.id})
            log_view = LogView()
            log_view.generate_log(request_data, param, "", track_fields)
            f = open(settings.MEDIA_ROOT + str(crud.get(self.table, "*", 'where id=' + pk)
                                               [0].get('owner_id')) + '/' + file_res.modified_file_name.split('.')[0] + '.html', 'w')
            f.write(request.data['data'].encode())
            f.close()
            os.chdir(settings.MEDIA_ROOT + str(crud.get(self.table,
                                                        "*", 'where id=' + pk)[0].get('owner_id')))
            os.system('unoconv --format=' + file_res.name.split('.')[-1] + ' ' + settings.MEDIA_ROOT + str(crud.get(
                self.table, "*", 'where id=' + pk)[0].get('owner_id')) + '/' + file_res.modified_file_name.split('.')[0] + '.html')
            time.sleep(3)
            os.remove(settings.MEDIA_ROOT + str(crud.get(self.table, "*", 'where id=' + pk)
                                                [0].get('owner_id')) + '/' + file_res.modified_file_name.split('.')[0] + '.html')
            encrypt_file(os.getcwd() + '/' + file_res.modified_file_name, os.getcwd() +
                         '/' + base64.b16encode(file_res.modified_file_name), '123')
            os.remove(os.getcwd() + '/' + file_res.modified_file_name)
        return Response({"hai": 'hai'})

    # preview function
    @detail_route(methods=['get'], url_path='preview', permission_classes=(AllowAny,))
    def pdf_editor(self, request, pk=None, *args, **kwargs):
        file_res = File.objects.get(id=pk)
        decrypt_file(os.path.join(settings.MEDIA_ROOT + str(crud.get(self.table, "*", 'where id=' + pk)[0].get('owner_id')) + '/' + base64.b16encode(
            file_res.modified_file_name)), os.path.join(settings.MEDIA_ROOT + file_res.modified_file_name), '123')
        os.chdir(settings.MEDIA_ROOT + str(crud.get(self.table,
                                                    "*", 'where id=' + pk)[0].get('owner_id')))
        os.system('unoconv --format=pdf ' +
                  os.path.join(settings.MEDIA_ROOT + file_res.modified_file_name))
        file = open(settings.MEDIA_ROOT +
                    file_res.modified_file_name.split('.')[0] + '.pdf', 'rb')
        response = HttpResponse(FileWrapper(
            file), content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="{}"'.format(
            file_res.modified_file_name)
        os.remove(os.path.join(settings.MEDIA_ROOT +
                               file_res.modified_file_name))
        os.remove(settings.MEDIA_ROOT +
                  file_res.modified_file_name.split('.')[0] + '.pdf')
        return response

    @detail_route(methods=["get"], url_path="related-files")
    def get_related_files(self, request, pk=None, *args):
        try:
            files = crud.execute("select id from file_manager_file where id in (select file_id from file_manager_file_tags where tag_id in (select tag_id from file_manager_file_tags where file_id = {0})) order by created_date desc"
                                 .format(int(pk)))
            files = zip(*files)[0] if files and files[0] else False
            if files is not False:
                file_object = File.objects.filter(
                    id__in=files).order_by(c.name)
                shared = FileSerializer(file_object, many=True)
                return Response(shared.data)
            else:
                return Response([])

        except Exception as e:
            return Response({"error": e})

    def list(self, request, *args, **kwargs):
        """Overridden GET For File Informations Created by a Particular Owner """
        try:
            response = request.user.id
            file_info = crud.get(self.table, "*", "where owner_id = " +
                                 str(response) + " order by created_date desc")
            shared_files = self.get_file_data(request, file_info)
            shared_info = map(lambda i: i.update({'tags': [item for sublist in crud.execute("select tag_id from  file_manager_file_tags where file_id = %s " % (
                i['id'])) for item in sublist], 'shared_ids': crud.get(ShareView.table, "*", "where file_id = %s " % (i['id']))}), file_info)
            return Response(file_info)
        except Exception as e:
            return Response(e)

    def retrieve(self, request, pk=None, *args, **kwargs):
        """Overridden GET For Particular File Informations about Shared & its Tags"""
        try:
            file_request = int(pk)
            file_info = crud.get(
                self.table, "*", "where id = %s order by created_date desc" % (file_request))
            file_info = file_info and file_info[0]
            shared_info = crud.get(ShareView.table, "*",
                                   "where file_id = %s " % (file_request))
            tag_info = crud.execute(
                "select tag_id from  file_manager_file_tags where file_id = %s " % (file_request))
            tag_info = zip(*tag_info)[0] if tag_info and tag_info[0] else []
            shared_files = self.get_file_data(request, [file_info])
            return Response(file_info)
        except Exception as e:
            return Response(e)

    @list_route(methods=["get"], url_path="totaldocuments")
    def totaldocuments(self, request, *args, **kwargs):
        """Total Documents for an Owner/User in Dashboard"""
        total_documents_userid = request.user.id
        my_total_documents = crud.get("file_manager_file",["count(id) as my_file"],"where owner_id = %s" % (total_documents_userid))
        my_total_documents =  my_total_documents and my_total_documents [0]
        my_shared_documents = crud.execute("SELECT share_id FROM file_manager_share_user_ids WHERE user_id = %s" % (total_documents_userid))
        my_shared_documents = zip(*my_shared_documents)
        
        try:
            my_shared_documents1 = crud.get("file_manager_share",["count(file_id)"]," WHERE file_id is not null and id in {}" .format(my_shared_documents[0])) if len(my_shared_documents) >1 else crud.get("file_manager_share",["count(file_id)"]," WHERE file_id is not null and id = {}" .format(my_shared_documents[0][0]))
        except Exception as err:
            return Response(err)
        my_shared_documents1 = my_shared_documents1 and my_shared_documents1[0]
        my_total_documents.update(my_shared_documents1)
        return Response(my_total_documents) 

    @list_route(methods=["get"], url_path="mytasks")
    def get_mytasks(self, request, *args, **kwargs):
        "Custom Service for My Tasks in Dashboard for an Owner/User"
        my_tasks_userid = request.user.id
        my_taks_fileinfo = crud.execute("""select id from file_manager_file  where workflow_id in(select id from ntwf_workflow where is_template='false' and id in
                           (select workflow_id from ntwf_transition where auth_user_id = %s ) and active_state_id in (select state_from_id from ntwf_transition) )""" % (my_tasks_userid))
        my_tasks_fileinfo1 = map(lambda i: crud.get(
            self.table, "*", "where id = %s" % (i))[0], my_taks_fileinfo)
        return Response(my_tasks_fileinfo1)

    @list_route(methods=["get"], url_path="mypendingtasks")
    def get_mypendingtasks(self, request, *args, **kwargs):
        """My Pending Requests in Dashboard"""
        my_pending_tasks_userid = request.user.id
        my_pendingtasks_fileinfo = crud.execute(crud.fetch_query(c.file_manager,c.my_pendingtasks_fileinfo).format(my_pending_tasks_userid))
        my_pendingtasks_fileinfo1 = map(lambda i: crud.get(self.table, "*", "where id = %s" % (i[0]))[0], my_pendingtasks_fileinfo)
        return Response(my_pendingtasks_fileinfo1)


class TagView(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    table = Tag._meta.db_table

    def list(self, request, *args, **kwargs):
        res = crud.get(self.table, c.all)
        logger.debug("Info {} \n request: {}".format(res, request.__dict__))
        return Response(res)


class ShareView(ModelViewSet):
    queryset = Share.objects.all()
    serializer_class = ShareSerializer
    table = Share._meta.db_table


class ShareView(ModelViewSet):
    queryset = Share.objects.all()
    serializer_class = ShareSerializer
    table = Share._meta.db_table
