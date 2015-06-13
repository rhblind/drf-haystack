# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from drf_haystack.serializers import HaystackSerializer
from .search_indexes import MockPersonIndex, MockLocationIndex


class SearchSerializer(HaystackSerializer):

    class Meta:
        index_classes = [MockPersonIndex, MockLocationIndex]
        fields = ["firstname", "lastname", "full_name"]

