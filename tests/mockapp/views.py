# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from drf_haystack.viewsets import HaystackViewSet
from drf_haystack.generics import SQHighlighterMixin

from .models import MockPerson, MockLocation
from .serializers import SearchSerializer, HighlighterSerializer, MoreLikeThisSerializer


class SearchViewSet1(SQHighlighterMixin, HaystackViewSet):
    index_models = [MockPerson, MockLocation]
    serializer_class = SearchSerializer


class SearchViewSet2(HaystackViewSet):
    index_models = [MockPerson, MockLocation]
    serializer_class = HighlighterSerializer


class SearchViewSet3(HaystackViewSet):
    index_models = [MockPerson]
    serializer_class = MoreLikeThisSerializer
