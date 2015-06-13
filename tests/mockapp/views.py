# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from drf_haystack.viewsets import HaystackViewSet

from .models import MockPerson, MockLocation
from .serializers import SearchSerializer


class SearchViewSet(HaystackViewSet):
    index_models = [MockPerson, MockLocation]
    serializer_class = SearchSerializer

