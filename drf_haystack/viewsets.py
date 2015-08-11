# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from itertools import chain
from dateutil.parser import parse

from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework.viewsets import ViewSetMixin
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin

from .generics import HaystackGenericAPIView


class HaystackViewSet(RetrieveModelMixin, ListModelMixin, ViewSetMixin, HaystackGenericAPIView):
    """
    The HaystackViewSet class provides the default `list()` and
    `retrieve()` actions with a haystack index as it's data source.
    """

    @list_route(methods=["get"], url_path="facets")
    def facets(self, request):
        """
        Sets up a list route for ``facet`` results.
        This will add ie. ^search/facets/$ to your existing ^search pattern.

        """
        filters = request.GET.copy()
        queryset = self.filter_queryset(self.get_queryset())

        for field in chain(filters, self.facet_fields):
            serializer_klass = self.get_serializer_class()

            if any(filter(lambda obj: hasattr(obj, field), serializer_klass.Meta.index_classes)):
                if field in self.date_facet_fields:
                    # Date faceting requires the following query
                    # parameters in order to construct the filter.
                    # term=<start_date>,<end_date>,<gap_by> and optionally <gap_amount>
                    terms = filters[field].split(",")
                    if not len(terms) in (3, 4):
                        continue

                    start_date, end_date, gap_by = iter(terms[0:3])
                    valid_gap = ("year", "month", "day", "hour", "minute", "second")
                    if gap_by not in valid_gap:
                        raise ValueError("The 'gap_by' parameter must be one of %s." % ", ".join(valid_gap))
                    try:
                        kwargs = {
                            "start_date": parse(start_date),
                            "end_date": parse(end_date),
                            "gap_by": gap_by,
                            "gap_amount": terms[-1:] if len(terms) == 4 else 1
                        }
                        queryset = queryset.date_facet(field, **kwargs)
                    except ValueError:
                        raise ValueError("Could not parse date string. Make sure to provide a string "
                                         "format readable for the `python-dateutil` library.")

                elif field in self.facet_fields:
                    queryset = queryset.facet(field)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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
