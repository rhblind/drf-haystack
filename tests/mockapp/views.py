# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals


from drf_haystack.filters import HaystackBoostFilter, HaystackHighlightFilter, HaystackAutocompleteFilter
from drf_haystack.generics import SQHighlighterMixin
from drf_haystack.viewsets import HaystackViewSet

from .models import MockPerson, MockLocation
from .serializers import (
    SearchSerializer, HighlighterSerializer,
    MoreLikeThisSerializer, MockPersonFacetSerializer
)


class SearchViewSet1(HaystackViewSet):
    index_models = [MockPerson]
    serializer_class = SearchSerializer
    filter_backends = [HaystackHighlightFilter, HaystackAutocompleteFilter]

    # Faceting
    facet_serializer_class = MockPersonFacetSerializer


class SearchViewSet2(HaystackViewSet):
    index_models = [MockPerson, MockLocation]
    serializer_class = HighlighterSerializer


class SearchViewSet3(HaystackViewSet):
    index_models = [MockPerson]
    serializer_class = MoreLikeThisSerializer
