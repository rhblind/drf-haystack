# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url

from rest_framework import routers

from .mockapp.views import SearchViewSet


router = routers.DefaultRouter()
router.register("search", viewset=SearchViewSet, base_name="search")

urlpatterns = patterns(
    "",
    url(r"^", include(router.urls))
)
