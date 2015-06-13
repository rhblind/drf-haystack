# -*- coding: utf-8 -*-
#
# Unit tests for the `drf_haystack.viewsets` classes.
#

from __future__ import absolute_import, unicode_literals

from django.test import TestCase
from haystack.query import SearchQuerySet
from rest_framework import status
from rest_framework.serializers import Serializer
from rest_framework.test import APIRequestFactory

from drf_haystack.viewsets import HaystackViewSet

from .mockapp.models import MockPerson
from .mockapp.search_indexes import MockPersonIndex


factory = APIRequestFactory()


class HaystackViewSetTestCase(TestCase):

    fixtures = ["mockperson"]

    def setUp(self):
        MockPersonIndex().reindex()

        class ViewSet(HaystackViewSet):
            serializer_class = Serializer

        self.view = ViewSet

    def tearDown(self):
        MockPersonIndex().clear()

    def test_get_queryset_no_queryset(self):
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_queryset_with_queryset(self):
        setattr(self.view, "queryset", SearchQuerySet().all())
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_queryset_with_index_models(self):
        setattr(self.view, "index_models", [MockPerson])
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_object(self):
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view.as_view(actions={"get": "retrieve"})(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_obj_raise_404(self):
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view.as_view(actions={"get": "retrieve"})(request, pk=100000)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_object_invalid_lookup_field(self):
        request = factory.get(path="/", data="", content_type="application/json")
        self.assertRaises(
            AttributeError,
            self.view.as_view(actions={"get": "retrieve"}), request, invalid_lookup=1
        )

    def test_get_obj_override_lookup_field(self):
        setattr(self.view, "lookup_field", "custom_lookup")
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view.as_view(actions={"get": "retrieve"})(request, custom_lookup=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

