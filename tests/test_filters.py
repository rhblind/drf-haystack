# -*- coding: utf-8 -*-
#
# Unit tests for the `drf_haystack.filters` classes.
#

from __future__ import absolute_import, unicode_literals

from django.test import TestCase
from haystack.query import SearchQuerySet
from rest_framework import status
from rest_framework.serializers import Serializer
from rest_framework.test import APIRequestFactory

from drf_haystack.viewsets import HaystackViewSet

from .mockapp.models import MockLocation

factory = APIRequestFactory()


class HaystackFilterTestCase(TestCase):

    def setUp(self):

        class ViewSet(HaystackViewSet):

# class HaystackViewSetTestCase(TestCase):
#
#     def setUp(self):
#
#         class DefaultValuesViewSet(HaystackViewSet):
#             serializer_class = Serializer
#
#         self.view = DefaultValuesViewSet

