# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url

from rest_framework import routers

from .mockapp.views import SearchViewSet


router = routers.DefaultRouter()
router.register("person", viewset=SearchViewSet, base_name="search-person")

urlpatterns = patterns(
    "",
    url(r"^search/", include(router.urls))
)
