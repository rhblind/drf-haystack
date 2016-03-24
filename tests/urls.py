# -*- coding: utf-8 -*-

from django.conf.urls import include, url

from rest_framework import routers

from tests.mockapp.views import SearchViewSet1, SearchViewSet2, SearchViewSet3

router = routers.DefaultRouter()
router.register("search1", viewset=SearchViewSet1, base_name="search1")
router.register("search2", viewset=SearchViewSet2, base_name="search2")
router.register("search3", viewset=SearchViewSet3, base_name="search3")

urlpatterns = [
    url(r"^", include(router.urls))
]
