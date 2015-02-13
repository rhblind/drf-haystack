# -*- coding: utf-8 -*-
#
# Unit tests for the `drf_haystack.filters` classes.
#

from __future__ import absolute_import, unicode_literals

from django.test import TestCase
from rest_framework import status
from rest_framework import serializers
from rest_framework.test import APIRequestFactory

from drf_haystack.viewsets import HaystackViewSet
from drf_haystack.serializers import HaystackSerializer
from drf_haystack.filters import HaystackAutocompleteFilter, HaystackGEOSpatialFilter

from .constants import DATA_SET_SIZE
from .mockapp.models import MockLocation
from .mockapp.search_indexes import MockLocationIndex

factory = APIRequestFactory()


class HaystackFilterTestCase(TestCase):

    def setUp(self):

        class Serializer(HaystackSerializer):

            class Meta:
                index_classes = [MockLocationIndex]
                fields = [
                    "text", "address", "city", "zip_code",
                    "autocomplete"  # Ignoring the `coordinates` field
                ]
                field_aliases = {
                    "q": "autocomplete"
                }

        class ViewSet(HaystackViewSet):

            index_models = [MockLocation]
            serializer_class = Serializer
            # No need to specify `filter_backends`, defaults to HaystackFilter

        self.view = ViewSet

    def test_no_filters(self):
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), DATA_SET_SIZE)


class HaystackGEOSpatialFilterTestCase(TestCase):

    def setUp(self):

        class DistanceSerializer(serializers.Serializer):
            m = serializers.FloatField()
            km = serializers.FloatField()

        class Serializer(HaystackSerializer):
            distance = serializers.SerializerMethodField()

            class Meta:
                index_classes = [MockLocationIndex]
                fields = [
                    "text", "address", "city", "zip_code",
                    "coordinates",
                ]

                def get_distance(self, obj):
                    if hasattr(obj, "distance"):
                        return DistanceSerializer(obj.distance, many=False).data
                    return None

        class ViewSet(HaystackViewSet):
            index_models = [MockLocation]
            serializer_class = Serializer
            filter_backends = [HaystackGEOSpatialFilter]

        self.view = ViewSet