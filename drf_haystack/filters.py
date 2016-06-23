# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import operator

from django.utils import six
from haystack.query import SearchQuerySet
from rest_framework.filters import BaseFilterBackend

from drf_haystack.query import BoostQueryBuilder, FilterQueryBuilder, FacetQueryBuilder, SpatialQueryBuilder


class BaseHaystackFilterBackend(BaseFilterBackend):
    """
    A base class from which all Haystack filter backend classes should inherit.
    """

    query_builder_class = None

    @staticmethod
    def get_request_filters(request):
        return request.query_params.copy()

    def apply_filters(self, queryset, applicable_filters=None, applicable_exclusions=None):
        """
        Apply constructed filters and excludes and return the queryset

        :param queryset: queryset to filter
        :param applicable_filters: filters which are passed directly to queryset.filter()
        :param applicable_exclusions: filters which are passed directly to queryset.exclude()
        :returns filtered queryset
        """
        if applicable_filters:
            queryset = queryset.filter(applicable_filters)
        if applicable_exclusions:
            queryset = queryset.exclude(applicable_exclusions)
        return queryset

    def build_filters(self, view, filters=None):
        """
        Get the query builder instance and return constructed query filters.
        """
        query_builder = self.get_query_builder(backend=self, view=view)
        return query_builder.build_query(**(filters if filters else {}))

    def process_filters(self, filters, queryset, view):
        """
        Convenient hook to do any post-processing of the filters before they
        are applied to the queryset.
        """
        return filters

    def filter_queryset(self, request, queryset, view):
        """
        Return the filtered queryset.
        """
        applicable_filters, applicable_exclusions = self.build_filters(view, filters=self.get_request_filters(request))
        return self.apply_filters(
            queryset=queryset,
            applicable_filters=self.process_filters(applicable_filters, queryset, view),
            applicable_exclusions=self.process_filters(applicable_exclusions, queryset, view)
        )

    def get_query_builder(self, *args, **kwargs):
        """
        Return the query builder class instance that should be used to
        build the query which is passed to the search engine backend.
        """
        query_builder = self.get_query_builder_class()
        return query_builder(*args, **kwargs)

    def get_query_builder_class(self):
        """
        Return the class to use for building the query.
        Defaults to using `self.query_builder_class`.

        You may want to override this if you need to provide different
        methods of building the query sent to the search engine backend.
        """
        assert self.query_builder_class is not None, (
            "'%s' should either include a `query_builder_class` attribute, "
            "or override the `get_query_builder_class()` method." % self.__class__.__name__
        )
        return self.query_builder_class


class HaystackFilter(BaseHaystackFilterBackend):
    """
    A filter backend that compiles a haystack compatible filtering query.
    """

    query_builder_class = FilterQueryBuilder
    default_operator = operator.and_


class HaystackAutocompleteFilter(HaystackFilter):
    """
    A filter backend to perform autocomplete search.

    Must be run against fields that are either `NgramField` or
    `EdgeNgramField`.
    """

    def process_filters(self, filters, queryset, view):
        if not filters:
            return filters

        query_bits = []
        for field_name, query in filters.children:
            for word in query.split(" "):
                bit = queryset.query.clean(word.strip())
                kwargs = {
                    field_name: bit
                }
                query_bits.append(view.query_object(**kwargs))
        return six.moves.reduce(operator.and_, filter(lambda x: x, query_bits))


class HaystackGEOSpatialFilter(BaseHaystackFilterBackend):
    """
    A base filter backend for doing geo spatial filtering.
    If using this filter make sure to provide a `point_field` with the name of
    your the `LocationField` of your index.

    We'll always do the somewhat slower but more accurate `dwithin`
    (radius) filter.
    """

    query_builder_class = SpatialQueryBuilder
    point_field = "coordinates"

    def apply_filters(self, queryset, applicable_filters=None, applicable_exclusions=None):
        if applicable_filters:
            queryset = queryset.dwithin(**applicable_filters["dwithin"]).distance(**applicable_filters["distance"])
        return queryset

    def filter_queryset(self, request, queryset, view):
        return self.apply_filters(queryset, self.build_filters(view, filters=self.get_request_filters(request)))


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
        if self.get_request_filters(request) and isinstance(queryset, SearchQuerySet):
            queryset = queryset.highlight()
        return queryset


class HaystackBoostFilter(BaseHaystackFilterBackend):
    """
    Filter backend for applying term boost on query time.

    Apply by adding a comma separated ``boost`` query parameter containing
    a the term you want to boost and a floating point or integer for
    the boost value. The boost value is based around ``1.0`` as 100% - no boost.

    Gives a slight increase in relevance for documents that include "banana":
        /api/v1/search/?boost=banana,1.1
    """

    query_builder_class = BoostQueryBuilder
    query_param = "boost"

    def apply_filters(self, queryset, applicable_filters=None, applicable_exclusions=None):
        if applicable_filters:
            queryset = queryset.boost(**applicable_filters)
        return queryset

    def filter_queryset(self, request, queryset, view):
        return self.apply_filters(queryset, self.build_filters(view, filters=self.get_request_filters(request)))


class HaystackFacetFilter(BaseHaystackFilterBackend):
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

    query_builder_class = FacetQueryBuilder

    def apply_filters(self, queryset, applicable_filters=None, applicable_exclusions=None):
        """
        Apply faceting to the queryset
        """
        for field, options in applicable_filters["field_facets"].items():
            queryset = queryset.facet(field, **options)

        for field, options in applicable_filters["date_facets"].items():
            queryset = queryset.date_facet(field, **options)

        for field, options in applicable_filters["query_facets"].items():
            queryset = queryset.query_facet(field, **options)

        return queryset

    def filter_queryset(self, request, queryset, view):
        return self.apply_filters(queryset, self.build_filters(view, filters=self.get_request_filters(request)))
