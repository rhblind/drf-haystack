# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import operator
import warnings
from itertools import chain


from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import six

import haystack
from haystack.query import SearchQuerySet

from rest_framework.filters import BaseFilterBackend

from .query import QueryBuilder


class HaystackFilter(BaseFilterBackend):
    """
    A filter backend that compiles a haystack compatible
    filtering query.
    """

    query_builder = QueryBuilder()

    @staticmethod
    def get_request_filters(request):
        return request.GET.copy()

    @classmethod
    def build_filter(cls, view, filters=None):
        """
        Creates a single SQ filter from querystring parameters that
        correspond to the SearchIndex fields that have been "registered"
        in `view.fields`.

        Default behavior is to `OR` terms for the same parameters, and `AND`
        between parameters.

        Any querystring parameters that are not registered in
        `view.fields` will be ignored.
        """
        return cls.query_builder.build_query(view, **(filters if filters else {}))

    def filter_queryset(self, request, queryset, view):
        applicable_filters, applicable_exclusions = self.build_filter(view, filters=self.get_request_filters(request))
        if applicable_filters:
            queryset = queryset.filter(applicable_filters)
        if applicable_exclusions:
            queryset = queryset.exclude(applicable_exclusions)
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

        applicable_filters, applicable_exclusions = self.build_filter(view, filters=self.get_request_filters(request))

        if applicable_filters:
            queryset = queryset.filter(self._construct_query(applicable_filters, queryset, view))
        if applicable_exclusions:
            queryset = queryset.exclude(self._construct_query(applicable_exclusions, queryset, view))

        return queryset

    def _construct_query(self, terms, queryset, view):
        query_bits = []
        for field_name, query in terms.children:
            for word in query.split(" "):
                bit = queryset.query.clean(word.strip())
                kwargs = {
                    field_name: bit
                }
                query_bits.append(view.query_object(**kwargs))
        return six.moves.reduce(operator.and_, filter(lambda x: x, query_bits))


class BaseHaystackGEOSpatialFilter(HaystackFilter):
    """
    A base filter backend for doing geospatial filtering.
    If using this filter make sure to provide a `point_field` with the name of
    your the `LocationField` of your index.

    We'll always do the somewhat slower but more accurate `dwithin`
    (radius) filter.
    """
    point_field = None

    def __init__(self, *args, **kwargs):
        if not self.point_field:
            raise ImproperlyConfigured("You should provide `point_field` in "
                                       "your subclassed geo-spatial filter "
                                       "class.")
        try:
            from haystack.utils.geo import D, Point
            self.D = D
            self.Point = Point
        except ImportError as e:  # pragma: no cover
            warnings.warn("Make sure you've installed the `libgeos` library.\n "
                          "(`apt-get install libgeos` on linux, or `brew install geos` on OS X.)")
            raise e

    def unit_to_meters(self, distance_obj):
        """
        Emergency fix for https://github.com/toastdriven/django-haystack/issues/957
        According to Elasticsearch documentation, units are always measured in meters unless
        explicitly declared otherwise. It seems that the unit description is lost somewhere,
        so everything ends up in the query without any unit values, thus the value is calculated
        in meters.
        """
        return self.D(m=distance_obj.m * 1000)  # pragma: no cover

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

        filters = dict((k, filters[k]) for k in chain(self.D.UNITS.keys(), ["from"]) if k in filters)
        distance = dict((k, v) for k, v in filters.items() if k in self.D.UNITS.keys())
        if "from" in filters and len(filters["from"].split(",")) == 2:
            try:
                latitude, longitude = map(float, filters["from"].split(","))
                point = self.Point(longitude, latitude, srid=getattr(settings, "GEO_SRID", 4326))
                if point and distance:
                    major, minor, _ = haystack.__version__
                    if queryset.query.backend.__class__.__name__ == "ElasticsearchSearchBackend" \
                            and (major == 2 and minor < 4):
                        distance = self.unit_to_meters(self.D(**distance))  # pragma: no cover
                    else:
                        distance = self.D(**distance)
                    queryset = queryset.dwithin(self.point_field, point, distance).distance(self.point_field, point)
            except ValueError:
                raise ValueError("Cannot convert `from=latitude,longitude` query parameter to "
                                 "float values. Make sure to provide numerical values only!")

        return queryset

    def filter_queryset(self, request, queryset, view):
        queryset = self.geo_filter(queryset, filters=self.get_request_filters(request))
        return super(BaseHaystackGEOSpatialFilter, self).filter_queryset(request, queryset, view)


class HaystackGEOSpatialFilter(BaseHaystackGEOSpatialFilter):
    """
    If using this filter make sure your index has a `LocationField`
    named `coordinates`.
    """
    point_field = 'coordinates'


class HaystackHighlightFilter(HaystackFilter):
    """
    A filter backend which adds support for ``highlighting`` on the
    SearchQuerySet level (the fast one).
    Note that you need to use a search backend which supports highlighting
    in order to use this.

    This will add a ``hightlighted`` entry to your response, encapsulating the
    highlighted words in an `<em>highlighted results</em>` block.
    """

    def filter_queryset(self, request, queryset, view):
        queryset = super(HaystackHighlightFilter, self).filter_queryset(request, queryset, view)
        if request.GET and isinstance(queryset, SearchQuerySet):
            queryset = queryset.highlight()
        return queryset


class HaystackBoostFilter(HaystackFilter):
    """
    Filter backend for applying term boost on query time.

    Apply by adding a comma separated ``boost`` query parameter containing
    a the term you want to boost and a floating point or integer for
    the boost value. The boost value is based around ``1.0`` as 100% - no boost.

    Gives a slight increase in relevance for documents that include "banana":
        /api/v1/search/?boost=banana,1.1

    The boost is applied *after* regular filtering has occurred.
    """

    @staticmethod
    def apply_boost(queryset, filters):
        if "boost" in filters and len(filters["boost"].split(",")) == 2:
            term, boost = iter(filters["boost"].split(","))
            try:
                queryset = queryset.boost(term, float(boost))
            except ValueError:
                raise ValueError("Cannot convert boost to float value. Make sure to provide a "
                                 "numerical boost value.")
        return queryset

    def filter_queryset(self, request, queryset, view):
        queryset = super(HaystackBoostFilter, self).filter_queryset(request, queryset, view)
        return self.apply_boost(queryset, filters=self.get_request_filters(request))


class HaystackFacetFilter(HaystackFilter):
    """
    Filter backend for faceting search results.
    This backend does not apply regular filtering.

    Faceting field options can be set by using the ``field_options`` attribute
    on the serializer, and can be overridden by query parameters. Dates will be
    parsed by the ``python-dateutil.parser()`` which can handle most date formats.

    Query parameters is parsed in the following format:
      ?field1=option1:value1,option2:value2&field2=option1:value1,option2:value2
    where each options ``key:value`` pair is separated by the ``view.lookup_sep`` attribute.
    """

    # TODO: Support multiple indexes/serializers

    def build_facet_filter(self, view, filters=None):
        """
        Creates a dict of dictionaries suitable for passing to the
        SearchQuerySet ``facet``, ``date_facet`` or ``query_facet`` method.
        """
        return self.query_builder.build_facet_query(view, **(filters if filters else {}))

    @staticmethod
    def apply_facets(queryset, filters):
        """
        Apply faceting to the queryset
        """

        for field, options in filters["field_facets"].items():
            queryset = queryset.facet(field, **options)

        for field, options in filters["date_facets"].items():
            queryset = queryset.date_facet(field, **options)

        # TODO: Implement support for query faceting
        # for field, options in filters["query_facets"].items():
        #     continue

        return queryset

    def filter_queryset(self, request, queryset, view):
        return self.apply_facets(queryset, filters=self.build_facet_filter(view, self.get_request_filters(request)))
