# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import ViewSetMixin

from drf_haystack.generics import HaystackGenericAPIView


class HaystackViewSet(RetrieveModelMixin, ListModelMixin, ViewSetMixin, HaystackGenericAPIView):
    """
    The HaystackViewSet class provides the default ``list()`` and
    ``retrieve()`` actions with a haystack index as it's data source.
    """
    pass
