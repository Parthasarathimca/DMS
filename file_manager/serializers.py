from rest_framework.serializers import ModelSerializer,PrimaryKeyRelatedField
from .models import *


# class WorkFlowSerializers(ModelSerializer):

#     class Meta:
#         model = WorkFlow
#         fields = ['name']

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["id","last_login","is_superuser","username","first_name","last_name","email","is_staff","is_active","date_joined","groups","user_permissions"]


class ShareSerializer(ModelSerializer):
    class Meta:
        model = Share
        fields = ["can_read","can_write","can_delete","user_ids","group_ids","directory_id","file_id"]
 

class FileSerializer(ModelSerializer):
    shared_files = ShareSerializer(many=True,read_only=True)

    class Meta:
        model = File
        fields = '__all__'


class DirectorySerializer(ModelSerializer):
    
    file_ids = FileSerializer(many=True,read_only=True)
    shared_dirs = ShareSerializer(many=True,read_only=True)
    sub_directories = PrimaryKeyRelatedField(many=True,read_only=True)
    
    # directory_workflow = WorkFlowSerializers(many=True, read_only=True)

    class Meta:
        model = Directory
        # es_model = DirectoryIndex
        fields = '__all__'


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'
