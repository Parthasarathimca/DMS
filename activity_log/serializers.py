from rest_framework.serializers import ModelSerializer,PrimaryKeyRelatedField
from .models import *


# class WorkFlowSerializers(ModelSerializer):

#     class Meta:
#         model = WorkFlow
#         fields = ['name']

class ActivitySerializer(ModelSerializer):
    class Meta:
        model = Activity
        fields = ['id','name','message','user_id','created_date']

class LogSerializer(ModelSerializer):
    
    related_activities = ActivitySerializer(many=True,read_only=True)
    class Meta: 
        model = Log
        fields = '__all__'