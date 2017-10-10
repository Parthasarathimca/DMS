"""dms URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from rest_framework.routers import DefaultRouter
from file_manager import views
from file_manager import elastic_search
from activity_log import views as ActivityView
from ntwf import views as ntwf_views
from django.http import HttpResponse
from django.conf.urls import (
    handler400, handler403, handler404, handler500
)   
from rest_framework_jwt.views import obtain_jwt_token, verify_jwt_token

from rest_framework_swagger.views import get_swagger_view
schema_view = get_swagger_view(title='API Doc')
import  file_manager

router = DefaultRouter()
router.register(r'log', ActivityView.LogView)
router.register(r'activity', ActivityView.ActivityView)
router.register(r'directories', views.DirectoryView)
router.register(r'users', views.UserView)
router.register(r'files', views.FileView)
router.register(r'tags', views.TagView)
# router.register(r'workflows', views.WorkFlowView)
router.register(r'users', ntwf_views.UserViewSet)
router.register(r'groups', ntwf_views.GroupViewSet)
router.register(r'workflows', ntwf_views.WorkflowViewSet)
router.register(r'transitions', ntwf_views.TransitionViewSet)
router.register(r'states', ntwf_views.StateViewSet)

urlpatterns = [
    url(r'^admin/', admin.site.urls, name="Administrator"),
    url(r'^', include(router.urls), name="Home"),
    url(r'^api-docs', schema_view, name="API Doc"),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api-token-auth/', obtain_jwt_token),
    url(r'^api-token-verify/', verify_jwt_token),
    url(r'^search/(?P<name>[^/.]+)/$',elastic_search.els_view,name='search'),
    # url(r'^search/', include('file_manager.urls'),name="Search"),
    url(r'^login/', include('activity_log.urls')), 


]

handler403 = 'ntwf_views.StateViewSet.error'
