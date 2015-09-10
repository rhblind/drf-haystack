# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

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

    # @list_route(methods=["get"], url_path="facets")
    # def facets(self, request):
    #     """
    #     Sets up a list route for ``faceted`` results.
    #     This will add ie. ^search/facets/$ to your existing ^search pattern.
    #
    #     """
    #     queryset = self.filter_queryset(self.get_queryset())
    #     # serializer_cls = self.get_serializer_class()
    #     # for facet in self.facet_fields:
    #     #     for field, defaults in six.iteritems(facet):
    #     #         if "type" not in defaults or defaults["type"] not in ("field", "date"):
    #     #             raise AttributeError("You must specify field type for the %s field. "
    #     #                                  "Valid types are 'field' and 'date'.")
    #     #         if any(filter(lambda obj: hasattr(obj, field), serializer_cls.Meta.index_classes)):
    #     #             if defaults["type"] == "date":
    #     #                 valid_gap = ("year", "month", "day", "hour", "minute", "second")
    #     #                 options = defaults.get("options", {})
    #     #                 if not all(("start_date", "end_date", "gap_by" in options)):
    #     #                     raise AttributeError("Date faceting requires a **options option with "
    #     #                                          "'start_date', 'end_date' and 'gap_by' to be set.")
    #     #                 if not options["gap_by"] in valid_gap:
    #     #                     raise ValueError("The 'gap_by' parameter must be one of %s." % ", ".join(valid_gap))
    #     #                 options.setdefault("gap_amount", 1)
    #     #                 queryset = queryset.date_facet(field, **options)
    #     #
    #     #             elif defaults["type"] == "field":
    #     #                 options = defaults.get("options", {})
    #     #                 queryset.facet(field, **options)
    #
    #     # page = self.paginate_queryset(queryset.facet_counts())
    #     # if page is not None:
    #     #     serializer = HaystackFacetSerializer(page, many=False)
    #     #     return self.get_paginated_response(serializer.data)
    #
    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response(serializer.data)

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
