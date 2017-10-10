# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.test import TestCase
from rest_framework.test import APIClient
client = APIClient()
client.login(username='next', password='next@123')
response = client.post(
'/directories/', {'name': 'new idea1', "owner_id": 1}, format='json')
print "response",response 
assert response.status_code == 200
from rest_framework.test import APIRequestFactory
from views import DirectoryView
from django.contrib.auth.models import User
from rest_framework.test import force_authenticate
from requests.auth import HTTPBasicAuth
from rest_framework.test import RequestsClient

from rest_framework.test import APIClient

client = APIClient()
client.login(username='next', password='next@123')
# API Tests
# Create New Directory
response = client.post(
    '/directories/', {'name': 'new idea1', "owner_id": 1}, format='json')
# print "response",response
assert response.status_code == 200 or 201
# Get All Directories
response = client.get(
    '/directories/', format='json')
assert response.status_code == 200
# Get Parent Directories
response = client.get(
    '/directories/
    parent-dirs/', format='json')
assert response.status_code == 200

response = client.get(
    '/directories/1/child-dirs/', format='json')
assert response.status_code == 200

response = client.get(
    '/directories/shared-dirs/', format='json')
assert response.status_code == 200

