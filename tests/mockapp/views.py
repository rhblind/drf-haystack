# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from rest_framework.pagination import PageNumberPagination

from drf_haystack.filters import HaystackFilter, HaystackBoostFilter, HaystackHighlightFilter, HaystackAutocompleteFilter, HaystackGEOSpatialFilter
from drf_haystack.viewsets import HaystackViewSet

from .models import MockPerson, MockLocation
from .serializers import (
    SearchSerializer, HighlighterSerializer,
    MoreLikeThisSerializer, MockPersonFacetSerializer
)


class BasicPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"


class SearchViewSet1(HaystackViewSet):
    index_models = [MockPerson]
    serializer_class = SearchSerializer
    filter_backends = [HaystackFilter, HaystackBoostFilter]

    # Faceting
    facet_serializer_class = MockPersonFacetSerializer
    pagination_class = BasicPagination


class SearchViewSet2(HaystackViewSet):
    index_models = [MockLocation]
    serializer_class = HighlighterSerializer
    filter_backends = [HaystackBoostFilter]


class SearchViewSet3(HaystackViewSet):
    index_models = [MockPerson]
    serializer_class = MoreLikeThisSerializer
