from elasticsearch import Elasticsearch
from pprint import pprint
from rest_framework.response import Response
from rest_framework.decorators import api_view,permission_classes
from django.http import HttpResponse
from rest_framework.permissions import AllowAny

@api_view(['GET'])
@permission_classes((AllowAny,))
def els_view(request,name=None):
	connection_es=Elasticsearch()
	values_cs=connection_es.search(index='dms_test',body={"query":{"query_string" :{"default_field" : "name", "query" : "*"+name+"*"}}}).get('hits').get('total')
	if values_cs!=0:values_cs=map(lambda x:x.get('_source'),connection_es.search(index='dms_test',body={"query":{"query_string" :{"default_field" : "name", "query" : "*"+name+"*"}}}).get('hits').get('hits'))
	else:values_cs='Nothing Found'
	return Response(values_cs)