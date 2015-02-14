# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import operator

from itertools import chain
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import six

from haystack.utils.geo import D, Point
from haystack.backends.elasticsearch_backend import ElasticsearchSearchBackend
from rest_framework.filters import BaseFilterBackend


class HaystackFilter(BaseFilterBackend):
    """
    A filter backend that compiles a haystack compatible
    filtering query.
    """

    @staticmethod
    def build_filter(view, filters=None):
        """
        Creates a single SQ filter from querystring parameters that
        correspond to the SearchIndex fields that have been "registered"
        in `view.fields`.

        Default behavior is to `OR` terms for the same parameters, and `AND`
        between parameters.

        Any querystring parameters that are not registered in
        `view.fields` will be ignored.
        """

        terms = []

        if filters is None:
            filters = {}  # pragma: no cover

        for param, value in filters.items():
            # Skip if the parameter is not listed in the serializer's `fields`
            # or if it's in the `exclude` list.
            if view.serializer_class:
                try:
                    if hasattr(view.serializer_class.Meta, "field_aliases"):
                        param = view.serializer_class.Meta.field_aliases.get(param, param)

                    fields = getattr(view.serializer_class.Meta, "fields", [])
                    exclude = getattr(view.serializer_class.Meta, "exclude", [])

                    if param not in fields or param in exclude or not value:
                        continue

                except AttributeError:
                    raise ImproperlyConfigured("%s must implement a Meta class." %
                                               view.serializer_class.__class__.__name__)

            tokens = value.split(view.lookup_sep)
            field_queries = []

            for token in tokens:
                if token:
                    field_queries.append(view.query_object((param, token)))

            terms.append(six.moves.reduce(operator.or_, filter(lambda x: x, field_queries)))

        return six.moves.reduce(operator.and_, filter(lambda x: x, terms)) if terms else []

    def filter_queryset(self, request, queryset, view):
        applicable_filters = self.build_filter(view, filters=request.GET.copy())
        if applicable_filters:
            queryset = queryset.filter(applicable_filters)
        return queryset


class HaystackAutocompleteFilter(HaystackFilter):
    """
    A filter backend to perform autocomplete search.

    Must be run against fields that are either `NgramField` or
    `EdgeNgramField`.
    """

    def filter_queryset(self, request, queryset, view):
        """
        Applying `applicable_filters` to the queryset by creating a
        single SQ filter using `AND`.
        """

        applicable_filters = self.build_filter(view, filters=request.GET.copy())

        if applicable_filters:
            query_bits = []
            for field_name, query in applicable_filters.children:
                for word in query.split(" "):
                    bit = queryset.query.clean(word.strip())
                    kwargs = {
                        field_name: bit
                    }
                    query_bits.append(view.query_object(**kwargs))
            queryset = queryset.filter(six.moves.reduce(operator.and_, filter(lambda x: x, query_bits)))

        return queryset


class HaystackGEOSpatialFilter(HaystackFilter):
    """
    A filter backend for doing geospatial filtering.
    If using this filter make sure your index has a `LocationField`
    named `coordinates`.

    We'll always do the somewhat slower but more accurate `dwithin`
    (radius) filter.
    """

    def unit_to_meters(self, distance_obj):
        """
        Emergency fix for https://github.com/toastdriven/django-haystack/issues/957
        According to Elasticsearch documentation, units are always measured in meters unless
        explicitly declared otherwise. It seems that the unit description is lost somewhere,
        so everything ends up in the query without any unit values, thus the value is calculated
        in meters.
        """
        return D(m=distance_obj.m * 1000)

    def geo_filter(self, queryset, filters=None):
        """
        Filter the queryset by looking up parameters from the query
        parameters.

        Expected query parameters are:
        - a `unit=value` parameter where the unit is a valid UNIT in the
          `django.contrib.gis.measure.Distance` class.
        - `from` which must be a comma separated longitude and latitude.

        Example query:
            /api/v1/search/?km=10&from=59.744076,10.152045

            Will perform a `dwithin` query within 10 km from the point
            with latitude 59.744076 and longitude 10.152045.
        """

        filters = dict((k, filters[k]) for k in chain(D.UNITS.keys(), ["from"]) if k in filters)
        distance = dict((k, v) for k, v in filters.items() if k in D.UNITS.keys())
        if "from" in filters and len(filters["from"].split(",")) == 2:
            try:
                latitude, longitude = map(float, filters["from"].split(","))
                point = Point(longitude, latitude, srid=getattr(settings, "GEO_SRID", 4326))
                if point and distance:
                    if isinstance(queryset.query.backend, ElasticsearchSearchBackend):
                        # TODO: Make sure this is only applied if using a malfunction elasticsearch backend!
                        # NOTE: https://github.com/toastdriven/django-haystack/issues/957
                        # FIXME: Remove when upstream haystack bug is resolved
                        distance = self.unit_to_meters(D(**distance))
                    queryset = queryset.dwithin("coordinates", point, distance).distance("coordinates", point)
            except ValueError:
                raise ValueError("Cannot convert `from=latitude,longitude` query parameter to "
                                 "float values. Make sure to provide numerical values only!")

        return queryset

    def filter_queryset(self, request, queryset, view):
        queryset = self.geo_filter(queryset, filters=request.GET.copy())
        return super(HaystackGEOSpatialFilter, self).filter_queryset(request, queryset, view)
