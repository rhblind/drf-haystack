# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from datetime import datetime, timedelta
from rest_framework.serializers import HyperlinkedIdentityField

from drf_haystack.serializers import HaystackSerializer, HaystackFacetSerializer, HighlighterMixin
from .search_indexes import MockPersonIndex, MockLocationIndex


class SearchSerializer(HaystackSerializer):

    class Meta:
        index_classes = [MockPersonIndex, MockLocationIndex]
        fields = [
            "firstname", "lastname", "full_name", "text",
            "address", "city", "zip_code",
        ]


class HighlighterSerializer(HighlighterMixin, HaystackSerializer):

    highlighter_css_class = "my-highlighter-class"
    highlighter_html_tag = "em"

    class Meta:
        index_classes = [MockPersonIndex, MockLocationIndex]
        fields = [
            "firstname", "lastname", "full_name",
            "address", "city", "zip_code",
        ]


class MoreLikeThisSerializer(HaystackSerializer):

    more_like_this = HyperlinkedIdentityField(view_name="search3-more-like-this", read_only=True)

    class Meta:
        index_classes = [MockPersonIndex]
        fields = [
            "firstname", "lastname", "full_name",
            "autocomplete"
        ]


class MockPersonFacetSerializer(HaystackFacetSerializer):

    class Meta:
        index_classes = [MockPersonIndex]
        fields = ["firstname", "lastname", "created"]
        field_options = {
            "firstname": {},
            "lastname": {},
            "created": {
                "start_date": datetime.now() - timedelta(days=3 * 365),
                "end_date": datetime.now(),
                "gap_by": "day",
                "gap_amount": 10
            }
        }
