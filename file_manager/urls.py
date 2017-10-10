# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)

from django.conf.urls import url

from .views import DictionaryElasticView

urlpatterns = [
    url(
        regex=r'^api/list$',
        view=DictionaryElasticView.as_view(),
        name='directory-list'
    ),
]