# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from dateutil import parser
from django.core.exceptions import ImproperlyConfigured

from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework.viewsets import ViewSetMixin
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin

from .generics import HaystackGenericAPIView


class HaystackViewSet(RetrieveModelMixin, ListModelMixin, ViewSetMixin, HaystackGenericAPIView):
    """
    The HaystackViewSet class provides the default ``list()`` and
    ``retrieve()`` actions with a haystack index as it's data source.
    """

    @detail_route(methods=["get"], url_path="more-like-this")
    def more_like_this(self, request, pk=None):
        """
        Sets up a detail route for ``more-like-this`` results.
        Note that you'll need backend support in order to take advantage of this.

        This will add ie. ^search/{pk}/more-like-this/$ to your existing ^search pattern.
        """
        queryset = self.filter_queryset(self.get_queryset())
        mlt_queryset = queryset.more_like_this(self.get_object().object)

        page = self.paginate_queryset(mlt_queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(mlt_queryset, many=True)
        return Response(serializer.data)


# class HaystackFacetViewSet(ListModelMixin, ViewSetMixin, HaystackGenericAPIView):
#     """
#     The HaystackFacetViewSet provides a default ``list()`` action as well as a
#     ``narrow()`` route for narrowing faceted results.
#
#     This ViewSet does not apply regular filtering and operates on the
#     ``SearchQuerySet().facet_counts()`` dictionary rather than the default ``SearchQuerySet()``.
#
#     Faceting field options can be set by using the ``field_options`` attribute
#     on the serializer, and will be overridden by query parameters if provided. Dates will be
#     parsed by the ``python-dateutil.parser()`` which can handle most formattings.
#
#     Query parameters is parsed in the following format:
#       ?field1=option1:value1,option2:value2&field2=option1:value1,option2:value2
#     where each option,value set is separated by the ``view.lookup_sep`` attribute.
#     """
#
#     # TODO: Fix a better way to update `field_options` from query parameters.
#     # TODO: Support multiple indexes/serializers
#     # TODO: Need to support multiple options separated by `view.lookup_sep`
#     # TODO: Need a better way to determine if to apply date or field faceting
#
#     @list_route(methods=["get"], url_path="narrow")
#     def narrow(self, request):
#         """
#         Sets up a list route for narrowing ``faceted`` results.
#         This will add ie. ^search-facet/narrow/$ to your existing ^search-facet pattern.
#         """
#
#         pass
#
#     def filter_queryset(self, queryset):
#
#         date_facets = {}
#         field_facets = {}
#         # query_facets = {}  # Not implemented yet!
#
#         serializer_cls = self.get_serializer_class()
#         try:
#             fields = getattr(serializer_cls.Meta, "fields", [])
#             exclude = getattr(serializer_cls.Meta, "exclude", [])
#             field_options = getattr(serializer_cls.Meta, "field_options", {})
#
#             for field, options in self.request.GET.items():
#
#                 if field not in fields or field in exclude:
#                     continue
#
#                 if field in field_options and len(options.split(":")) == 2:
#                     param, value = options.split(":")
#
#                     if param in ("start_date", "end_date"):
#                         value = parser.parse(value)
#
#                     defaults = field_options.pop(field, {})
#                     defaults.update({param: value})
#                     field_options[field] = defaults
#
#             for field, options in field_options.items():
#                 if any([k in options for k in ("start_date", "end_date", "gap_by", "gap_amount")]):
#                     valid_gap = ("year", "month", "day", "hour", "minute", "second")
#                     if not all(("start_date", "end_date", "gap_by" in options)):
#                         raise ValueError("Date faceting requires at least 'start_date', 'end_date' "
#                                          "and 'gap_by' to be set.")
#                     if not options["gap_by"] in valid_gap:
#                         raise ValueError("The 'gap_by' parameter must be one of %s." % ", ".join(valid_gap))
#                     options.setdefault("gap_amount", 1)
#                     date_facets[field] = field_options[field]
#
#                 else:
#                     # TODO: Should facet on fields with no options!
#                     field_facets[field] = field_options[field]
#
#         except AttributeError:
#             raise ImproperlyConfigured("%s must implement a Meta class." %
#                                        serializer_cls.__class__.__name__)
#
#         if field_facets:
#             for field, options in field_facets.items():
#                 queryset = queryset.facet(field, **options)
#         if date_facets:
#             for field, options in date_facets.items():
#                 queryset = queryset.date_facet(field, **options)
#
#         return [queryset.facet_counts()]
