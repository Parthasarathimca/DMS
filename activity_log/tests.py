# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.test import TestCase
from datetime import datetime
from rest_framework.test import APIClient
client = APIClient()
client.login(username='next', password='next@123')

response = client.post('/activity/',{"name": "test_name",
                 "message":"test_message",
                "activity_time":datetime.now(),"log_id":12,
                "user_id":1,
                "created_by_id":1, "created_date": datetime.now(),"modified_by_id":1, "modified_date": datetime.now()
                }   ,format='json')
print " 1.response",response 

assert response.status_code == 200 or 201

response = client.get('/activity/',format='json')
print "response",response 
assert response.status_code == 200 or 201



response = client.post('/log/',{
                        "created_by_id": 1, "created_date": datetime.now(),
                        "modified_date": datetime.now(),"modified_by_id":1}
                        ,format='json')
                
print " 2 .response",response 
print "response code ++",response.status_code
assert response.status_code == 200 or 201


response = client.get('/log/'
                        ,format='json')
                
print " 3 .response",response 
print "response code ++",response.status_code
assert response.status_code == 200 or 201


#custom get 
response = client.put('/activity/150',{'type':'file'}
                        ,format='json')                
print " 4@.response",response 
print "response code_activity",response.status_code
assert response.status_code == 200 or 201
#custom get 
response = client.put('/activity/140',{'type':'dir'}
                        ,format='json')                
print " 5 .response",response 
print "response code_activity",response.status_code
assert response.status_code == 200 or 201


#custom get version  
response = client.put('/activity/318',{'type':'version'}
                        ,format='json')                
print " 6 #.response",response 
print "response code_activity",response.status_code
assert response.status_code == 200 or 201










