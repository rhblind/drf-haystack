# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from datetime import datetime, timedelta

from drf_haystack.filters import HaystackBoostFilter, HaystackAutocompleteFilter
from drf_haystack.generics import SQHighlighterMixin
from drf_haystack.viewsets import HaystackViewSet

from .models import MockPerson, MockLocation
from .serializers import SearchSerializer, HighlighterSerializer, MoreLikeThisSerializer


class SearchViewSet1(HaystackViewSet):
    index_models = [MockPerson]
    facet_fields = [
        {"firstname": {}},
        {"lastname": {}}
    ]
    date_facet_fields = [{"created": {
        "start_date": datetime.now() - timedelta(days=3*365),
        "end_date": datetime.now(),
        "gap_by": "day",
        "gap_amount": 10
    }}]
    serializer_class = SearchSerializer
    filter_backends = [HaystackBoostFilter]


class SearchViewSet2(HaystackViewSet):
    index_models = [MockPerson, MockLocation]
    serializer_class = HighlighterSerializer


class SearchViewSet3(HaystackViewSet):
    index_models = [MockPerson]
    serializer_class = MoreLikeThisSerializer
    filter_backends = [HaystackBoostFilter]
