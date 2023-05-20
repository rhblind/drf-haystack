# -*- coding: utf-8 -*-

from django.urls import path
from django.conf.urls import include

from rest_framework import routers

from tests.mockapp.views import SearchPersonFacetViewSet, SearchPersonMLTViewSet

router = routers.DefaultRouter()
router.register(
    "search-person-facet",
    viewset=SearchPersonFacetViewSet,
    basename="search-person-facet",
)
router.register(
    "search-person-mlt", viewset=SearchPersonMLTViewSet, basename="search-person-mlt"
)

urlpatterns = [path("", include(router.urls))]
