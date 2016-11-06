# -*- coding: utf-8 -*-

from django.conf.urls import include, url

from rest_framework import routers

from tests.mockapp.views import SearchPersonFacetViewSet, SearchPersonMLTViewSet

router = routers.DefaultRouter()
router.register("search-person-facet", viewset=SearchPersonFacetViewSet, base_name="search-person-facet")
router.register("search-person-mlt", viewset=SearchPersonMLTViewSet, base_name="search-person-mlt")

urlpatterns = [
    url(r"^", include(router.urls))
]
