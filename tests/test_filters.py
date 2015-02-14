# -*- coding: utf-8 -*-
#
# Unit tests for the `drf_haystack.filters` classes.
#

from __future__ import absolute_import, unicode_literals
from django.core.exceptions import ImproperlyConfigured

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

    fixtures = ["mocklocation"]

    def setUp(self):

        MockLocationIndex().reindex()

        class Serializer1(HaystackSerializer):

            class Meta:
                index_classes = [MockLocationIndex]
                fields = [
                    "text", "address", "zip_code",
                    "autocomplete"  # Ignoring the `coordinates` field
                ]
                field_aliases = {
                    "q": "autocomplete"
                }

        class Serializer2(HaystackSerializer):

            class Meta:
                index_classes = [MockLocationIndex]
                exclude = [
                    "city"
                ]

        class Serializer3(HaystackSerializer):

            class Meta:
                index_classes = [MockLocationIndex]
                fields = ["text"]
                exclude = ["address"]
                # This is not allowed. Can't set both `fields` and `exclude`.

        class Serializer4(HaystackSerializer):
            # This is not allowed. Must implement a `Meta` class.
            pass

        class ViewSet1(HaystackViewSet):
            index_models = [MockLocation]
            serializer_class = Serializer1
            # No need to specify `filter_backends`, defaults to HaystackFilter

        class ViewSet2(ViewSet1):
            serializer_class = Serializer2

        class ViewSet3(ViewSet1):
            serializer_class = Serializer3

        class ViewSet4(ViewSet1):
            serializer_class = Serializer4

        self.view1 = ViewSet1
        self.view2 = ViewSet2
        self.view3 = ViewSet3
        self.view4 = ViewSet4

    def test_no_filters(self):
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view1.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), DATA_SET_SIZE)

    def test_filter_single_field(self):
        request = factory.get(path="/", data={"zip_code": "0289"})  # Should return 3 results
        response = self.view1.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_filter_single_field_OR(self):
        # Test filtering a single field for multiple values. The parameters should be OR'ed
        request = factory.get(path="/", data={"zip_code": "0289,0204"})  # Should return 5 results
        response = self.view1.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_filter_single_field_OR_custom_lookup_sep(self):
        setattr(self.view1, "lookup_sep", ";")
        request = factory.get(path="/", data={"zip_code": "0289;0204"})  # Should return 5 results
        response = self.view1.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

        # Reset the `lookup_sep`
        setattr(self.view1, "lookup_sep", ",")

    def test_filter_multiple_fields(self):
        # Test filtering multiple fields. The parameters should be AND'ed
        request = factory.get(path="/", data={"zip_code": "0289", "address": "Andersenhagen 8"})  # Should return 1 result
        response = self.view1.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_multiple_fields_OR_same_fields(self):
        # Test filtering multiple fields for multiple values. The values should be OR'ed between
        # same parameters, and AND'ed between them
        request = factory.get(path="/", data={
            "zip_code": "0289,0204",
            "address": "Andersenhagen 8,Fredriksenskogen 04"
        })  # Should return 2 result
        response = self.view1.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_excluded_field(self):
        request = factory.get(path="/", data={"city": "Oslo"}, content_type="application/json")
        response = self.view2.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), DATA_SET_SIZE)  # Should return all results since, field is ignored

    def test_raise_on_both_fields_and_exclude(self):
        # Make sure we're getting an ImproperlyConfigured when trying to call a viewset
        # which has both `fields` and `exclude` set.
        request = factory.get(path="/", data="", content_type="application/json")
        self.assertRaises(
            ImproperlyConfigured,
            self.view3.as_view(actions={"get": "list"}), request
        )

    def test_raise_on_serializer_without_meta_class(self):
        # Make sure we're getting an ImproperlyConfigured when trying to call a viewset with
        # a serializer with no `Meta` class.
        request = factory.get(path="", data="", content_type="application/json")
        self.assertRaises(
            ImproperlyConfigured,
            self.view4.as_view(actions={"get": "list"}), request
        )


class HaystackGEOSpatialFilterTestCase(TestCase):

    fixtures = ["mocklocation"]

    def setUp(self):

        MockLocationIndex().reindex()

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