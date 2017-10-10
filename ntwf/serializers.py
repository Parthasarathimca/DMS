from rest_framework.serializers import ModelSerializer
from models import WorkFlow, Transition, State
from django.contrib.auth.models import User, Group


class StateSerializer(ModelSerializer):

    class Meta:
        model = State
        fields = '__all__'


class TransitionSerializer(ModelSerializer):

    class Meta:
        model = Transition
        fields = '__all__'


class WorkflowSerializer(ModelSerializer):
    workflow_transition = TransitionSerializer(many=True, read_only=True)
    
    class Meta:
        model = WorkFlow
        fields = '__all__'
        




class GroupSerializer(ModelSerializer):    
    class Meta:
        model = Group
        fields = ('id','name')

class UserSerializer(ModelSerializer):    
    groups = GroupSerializer(many=True)
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'is_staff', 'groups',)
