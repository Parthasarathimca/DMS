# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework.viewsets import ModelViewSet
import crud
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
import logging
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from datetime import datetime
from django.conf import settings
import jsondiff as jd
import config,json
from rest_framework.decorators import api_view,permission_classes
from django.contrib.auth.models import User
from rest_framework import permissions
import requests
from rest_framework import status as st
logger = logging.getLogger(__name__)
events = {config.Created:config.Created, config.Updated:config.Updated,config.version:config.version}
global message
message = {}
# Create your views here.

@api_view([config.POST])
@permission_classes((permissions.AllowAny,))
def tranform_validation(request):
    auth_url= "http://"+request.META.get(config.HTTP_HOST)+config.api_token_auth
    data=json.loads(request.body.decode(config.utf8))
    username=data.get(config.username)
    password=data.get(config.password)
    print "data========>",data
    print "User name========>",username
    try:
        request_url =requests.get(config.transform_url+str(username)+'&'+config.password+'='+str(password))
        
        result = json.loads(request_url.text)
        print "Result  ====-=-=-=-=-=",result
        message=result.get(config.msg)
        data=result.get(config.info)
    except:
        data={config.username:username, config.password:password}
        headers = {config.content_type:config.application_json}
        token=requests.post(auth_url,data=json.dumps(data),headers=headers)
        return Response(token.content,status=st.HTTP_400_BAD_REQUEST)
        
    if message !=config.success:
        data={config.username:username, config.password:password}
        headers = {config.content_type:config.application_json}
        token=requests.post(auth_url,data=json.dumps(data),headers=headers)
        return Response(token.content,status=st.HTTP_400_BAD_REQUEST)

    elif message ==config.success:
        print "@@@@@TRan!for result",message
        #To check auth user table for user is exist or not
        user_check=crud.get(config.auth_user,[config.email],config.where_email.format(str(data.get(config.email))))
        if not user_check:
            user = User.objects.create_user(username=username,
                                 email=data.get(config.email),is_staff=True,is_superuser=True,
                                 password=password)
            data={ config.username:username,config.password:password}
            headers = {config.content_type: config.application_json}
            token=requests.post(auth_url,data=json.dumps(data),headers=headers)
            token=json.loads(token.text)
            return Response(token)
        else:
            data={config.username:username,config.password:password}
            headers = {config.content_type:config.application_json}
            token=requests.post(auth_url,data=json.dumps(data),headers=headers)
            token=json.loads(token.text)
            return Response(token)

class LogView(ModelViewSet):
    """
    @generate_log can get a requst and fields  and parameters to store a log while  either create or update event done
    @param request:Request to get insert data ,
    param : param to store the actvity log based on the param field,
    original_data : data can used to check the updated field and value,
    fields : Dynamic field value to generate message,
    @return: Actvity log Success or falilure message 
    """
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    table = Log._meta.db_table

    def generate_log(self, request, param=None, original_data=None, fields=None, ChangeTag=None):
        activity = ActivityView()
        #print "1=============================>param:",param,"\nreques",request,'\n === fileds',fields
        if param is not None:
            if fields is None:
                    table = Log._meta.db_table
                    name=config.Created
                    log_data = {
                        config.created_by_id: request.get(config.user_id), config.created_date: datetime.now(),
                        config.modified_date: datetime.now(),config.modified_by_id:request.get(config.user_id)}
                    log_data.update({param.get(config.field):request.get(config.id)})
                    id = crud.add(table,log_data) 
                    logger.debug(config.Generating_log.format(id))
                    if id:
                        if isinstance(id,int):
                            message=str(param.get(config.label))+" "+str(events.get(config.Created))
                            logger.debug(config.Create_message.format(message))
                            activity.generate_activity(request,events.get(config.Created),message,id)
                    else:
                        logger.error(config.Log_id_not_found,id)
            else:
#                print " 2 ====================================================param==>",param,'\n==> reques=>',request,'\n change tag',ChangeTag,'\n====,fileds',fields
                updated_value=[]
                message_data=[] 
                table = Log._meta.db_table
                if original_data and fields:
                    #change_value=jd.diff(original_data[0],request)
                    change_value=jd.diff((original_data),dict(request),syntax=config.symmetric)
                    updated_value = {key: value for key, value in change_value.items() if fields.get(key)}
                    if updated_value:
                        #updated_value = filter(lambda key:key  in fields,change_value)
                        mes={message_data.append(str(param.get(config.label))+' '+str(fields.get(k).get(config.label))+config.has_been_changed_from+str(updated_value.get(k)[0])+" to "+str(updated_value.get(k)[1])) for k in updated_value.keys()}
                        id=original_data.get(config.id)
                    else:
                        logger.debug(config.actvity_update.format(config.Track_fields_not_match))    
                        id=None        
                    if ChangeTag:
                        if config.Added in ChangeTag.keys():
                            name=config.Updated
                            msg=message_data.append(str(ChangeTag.get(config.Added).get(config.field)+" "+str( [j for i, j in enumerate(ChangeTag.get(config.Added).get(config.tag))])+" - "+ ChangeTag.get(config.Added).get(config.action)+" for "+str(param.get(config.label))+" "+request.get(config.name) ))    
                            id=original_data.get(config.id)
                        if config.Removed in ChangeTag.keys():
                            msg=message_data.append(str(ChangeTag.get(config.Removed).get(config.field)+" "+str( [j for i, j in enumerate(ChangeTag.get(config.Removed).get(config.tag))])+" - "+ ChangeTag.get(config.Removed).get(config.action)+" From "+str(param.get(config.label))+" "+request.get(config.name) ))
                            id=original_data.get(config.id)
                            name=config.Updated
                elif param.get(config.label)==config.Workflow:
                    id=param.get(config.workflow_id)
                    name=config.Updated
                    mes={message_data.append(str(param.get(config.label))+" "+config.has_been_changed_from+str(fields[0])+" to "+str(fields[1]))}
                    message={}
                    message.update({config.message:message_data})   
                
                elif param.get(config.action)==config.share:
                    id=request.get(param.get(config.field))
                    name=config.Updated
                    uname=[]
                    def get_name(self,table_name,parameters,id):
                        name=crud.get(table_name,parameters,config.where_id.format(id))
                        if table_name==config.auth_user:
                            name=str(name[0].get(parameters[0])+" "+name[0].get(parameters[1])).title()
                        if table_name==config.auth_group:
                            name=str(name[0].get(parameters[0])).title()
                        return name
                    permission=map(lambda k:fields.get(k) if request.get(k)!=False else None,[i for i  in fields.keys()])
                    if request.get(config.user_ids):
                        uname=map(lambda id:get_name(self,config.auth_user,[config.first_name,config.last_name],id),request.get(config.user_ids))
                        mes={message_data.append(str(param.get(config.label))+" "+config.share_user_msg+" "+str(uname)+" "+config.with_key+" "+str([p for p in permission if p !=   None ])+" "+config.permissions)}
                    if request.get(config.group_ids):
                        groups=map(lambda gid:get_name(self,config.auth_group,[config.name],gid),request.get(config.group_ids))
                        mes={message_data.append(str(param.get(config.label))+" "+config.share_group_msg+" "+str(groups)+" "+config.with_key+" "+str([p for p in permission if p !=   None ])+" "+config.permissions )}
                    message={}
                    message.update({config.message:message_data})  
                elif param.get(config.label)==config.version:
                   
                    id=param.get(config.file_id)
                    name=config.version
                    #verion_count=crud.execute(crud.fetch_query("activity_log","version_count").format(param.get(config.file_id)))
                    verion_count=crud.execute("select count(activity_log_log.id)from activity_log_log inner join activity_log_activity on activity_log_log.id=activity_log_activity.log_id where  activity_log_activity.name like '%version%' and file_id="+id)
                    verion_count=verion_count[0][0]
                    mes={message_data.append(str(param.get(config.label))+" "+str(verion_count+1))}
                    message={}
                    message.update({config.message:message_data}) 
                if id:
                    log=crud.get(self.table,config.all,config.where +param.get(config.field)+'='+str(id))
                    log_id=log[0].get(config.id)
                    if isinstance(log_id,int): 
                        for msg in message_data:
                            activity.generate_activity(request,events.get(name),msg,log_id)                       
                    else:
                        logger.debug(config.Log_id_not_found,log_id)        
                else:
                    logger.debug(config.Data_before_update_not_awailable)
        else:   
            Response(config.Parametter_missing)       

class ActivityView(ModelViewSet):
    """
    <h2>
    activity_data:
    Get complete log based on file or folder id\n
    </h2>
    """
    """
    @generate_activity generate_activity method can store the actvity againts the log table
    @param request:Request data is  to update activity table,
     event : Which event to be perfomed ,
     message : Message about perfomed event,
     log_id : Log table id.
    @list_route
        To display all activity log based on the selected control 
    @return: Actvity create Success or falilure message 
    """
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    table = Activity._meta.db_table

    def generate_activity(self, request, name, message, id):
        char = "[]'"
        for special_char in char:
            message = message.replace(special_char, "")
        try:
            table = Activity._meta.db_table
            activity_data = {config.name: name,
                    config.message:str(message),
                    config.activity_time:datetime.now(),config.log_id:id,
                    config.user_id:request.get(config.user_id), 
                    config.created_by_id: request.get(config.user_id), config.created_date: datetime.now(),config.modified_by_id:request.get(config.user_id), config.modified_date: datetime.now()
                    }  
        
            res = crud.add(table,activity_data)
            
        except Exception as e:
             return Response({config.error: e})
    @list_route(methods=[config.put], url_path=config.activity_url)
    def activity_data(self,request,activity_id=None, *args,**kwargs):
        activity_type=request.data.get(config.type)
        print "ACTIVITY TYPE +++===",activity_type
        if activity_id and activity_type is not int :
            if activity_type==config.dir:
                data = Log.objects.get(directory_id=activity_id)
            elif activity_type==config.file:
                data = Log.objects.get(file_id=activity_id)     
            elif activity_type=="wf":
                data = Log.objects.get(workflow_id=activity_id)     
            elif activity_type==config.version:
                version_data=crud.execute("select activity_log_activity.id from activity_log_log inner join activity_log_activity on activity_log_log.id=activity_log_activity.log_id where  activity_log_activity.name like '%version%' and file_id="+activity_id)
                version_data = zip(*version_data)
                if version_data:
                    if len(version_data[0])>1:
                        response = crud.get(ActivityView.table,"*", "where id in {}".format(version_data[0]))
                    else:
                        response = crud.get(ActivityView.table,"*", "where id={}".format(version_data[0][0]))
                            
                    data=response[0]
                
                    return Response(response)
                else:
                     logger.debug(config.Data_before_update_not_awailable)
                     return Response({config.status:0})

            if data:    
                response_data = LogSerializer(data)
                return Response(response_data.data)
            else:
                data=[]
        else:
            data=[] 
            return Response(data)
            
