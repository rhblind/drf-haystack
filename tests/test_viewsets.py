# -*- coding: utf-8 -*-
#
# Unit tests for the `drf_haystack.viewsets` classes.
#

from __future__ import absolute_import, unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from haystack.utils import Highlighter
from haystack.query import SearchQuerySet

from rest_framework import status
from rest_framework.serializers import Serializer
from rest_framework.test import APIRequestFactory

from drf_haystack.viewsets import HaystackViewSet
from drf_haystack.mixins import HighlighterMixin

from .mockapp.models import MockLocation

factory = APIRequestFactory()


class HaystackViewSetTestCase(TestCase):

    def setUp(self):

        class ViewSet(HaystackViewSet):
            serializer_class = Serializer

        self.view = ViewSet

    def test_viewset_get_queryset_no_queryset(self):
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewset_get_queryset_with_queryset(self):
        setattr(self.view, "queryset", SearchQuerySet().all())
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewset_get_queryset_with_index_models(self):
        setattr(self.view, "index_models", [MockLocation])
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewset_get_object(self):
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view.as_view(actions={"get": "retrieve"})(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewset_get_obj_raise_404(self):
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view.as_view(actions={"get": "retrieve"})(request, pk=82361)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_viewset_get_object_invalid_lookup_field(self):
        request = factory.get(path="/", data="", content_type="application/json")
        self.assertRaises(
            AttributeError,
            self.view.as_view(actions={"get": "retrieve"}), request, invalid_lookup=1
        )

    def test_viewset_get_obj_override_lookup_field(self):
        setattr(self.view, "lookup_field", "custom_lookup")
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view.as_view(actions={"get": "retrieve"})(request, custom_lookup=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class HaystackHighlightViewSetTestCase(TestCase):

    def setUp(self):

        class ViewSet(HighlighterMixin, HaystackViewSet):
            serializer_class = Serializer
            highlighter_class = Highlighter

        self.view = ViewSet

    def test_viewset_highlighter_context(self):
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view.as_view(actions={"get": "list"})(request)

    # def test_highlight_viewset_no_highlighter(self):
    #
    #     class ViewSet(HighlighterMixin, HaystackViewSet):
    #         serializer_class = Serializer
    #         highlighter_class = None
