# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals
from rest_framework.pagination import PageNumberPagination

from drf_haystack.filters import HaystackBoostFilter, HaystackHighlightFilter, HaystackAutocompleteFilter
from drf_haystack.generics import SQHighlighterMixin
from drf_haystack.viewsets import HaystackViewSet

from .models import MockPerson, MockLocation
from .serializers import (
    SearchSerializer, HighlighterSerializer,
    MoreLikeThisSerializer, MockPersonFacetSerializer
)


class BasicPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = "page_size"


class SearchViewSet1(HaystackViewSet):
    index_models = [MockPerson]
    serializer_class = SearchSerializer
    filter_backends = [HaystackHighlightFilter, HaystackAutocompleteFilter]

    # Faceting
    facet_serializer_class = MockPersonFacetSerializer
    pagination_class = BasicPagination


class SearchViewSet2(HaystackViewSet):
    index_models = [MockPerson, MockLocation]
    serializer_class = HighlighterSerializer


class SearchViewSet3(HaystackViewSet):
    index_models = [MockPerson]
    serializer_class = MoreLikeThisSerializer
