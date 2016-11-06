# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination

from drf_haystack.filters import HaystackFilter, HaystackBoostFilter, HaystackHighlightFilter, HaystackAutocompleteFilter, HaystackGEOSpatialFilter
from drf_haystack.viewsets import HaystackViewSet
from drf_haystack.mixins import FacetMixin, MoreLikeThisMixin

from .models import MockPerson, MockLocation
from .serializers import (
    SearchSerializer, HighlighterSerializer,
    MoreLikeThisSerializer, MockPersonFacetSerializer
)


class BasicPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"


class BasicLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 20


class SearchPersonFacetViewSet(FacetMixin, HaystackViewSet):
    index_models = [MockPerson]
    pagination_class = BasicLimitOffsetPagination
    serializer_class = SearchSerializer
    filter_backends = [HaystackFilter]

    # Faceting
    facet_serializer_class = MockPersonFacetSerializer


class SearchPersonMLTViewSet(MoreLikeThisMixin, HaystackViewSet):
    index_models = [MockPerson]
    serializer_class = MoreLikeThisSerializer
