# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from drf_haystack.filters import HaystackFacetFilter


class MoreLikeThisMixin(object):
    """
    Mixin class for supporting "more like this" on an API View.
    """

    @detail_route(methods=["get"], url_path="more-like-this")
    def more_like_this(self, request, pk=None):
        """
        Sets up a detail route for ``more-like-this`` results.
        Note that you'll need backend support in order to take advantage of this.

        This will add ie. ^search/{pk}/more-like-this/$ to your existing ^search pattern.
        """
        obj = self.get_object().object
        queryset = self.filter_queryset(self.get_queryset()).more_like_this(obj)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class FacetMixin(object):
    """
    Mixin class for supporting faceting on an API View.
    """

    facet_filter_backends = [HaystackFacetFilter]
    facet_serializer_class = None
    facet_objects_serializer_class = None
    facet_query_params_text = 'selected_facets'

    @list_route(methods=["get"], url_path="facets")
    def facets(self, request):
        """
        Sets up a list route for ``faceted`` results.
        This will add ie ^search/facets/$ to your existing ^search pattern.
        """
        queryset = self.filter_facet_queryset(self.get_queryset())

        for facet in request.query_params.getlist(self.facet_query_params_text):

            if ":" not in facet:
                continue

            field, value = facet.split(":", 1)
            if value:
                queryset = queryset.narrow('%s:"%s"' % (field, queryset.query.clean(value)))

        serializer = self.get_facet_serializer(queryset.facet_counts(), objects=queryset, many=False)
        return Response(serializer.data)

    def filter_facet_queryset(self, queryset):
        """
        Given a search queryset, filter it with whichever facet filter backends
        in use.
        """
        for backend in list(self.facet_filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)

        if self.load_all:
            queryset = queryset.load_all()

        return queryset

    def get_facet_serializer(self, *args, **kwargs):
        """
        Return the facet serializer instance that should be used for
        serializing faceted output.
        """
        assert "objects" in kwargs, "`objects` is a required argument to `get_facet_serializer()`"

        facet_serializer_class = self.get_facet_serializer_class()
        kwargs["context"] = self.get_serializer_context()
        kwargs["context"].update({
            "objects": kwargs.pop("objects"),
            "facet_query_params_text": self.facet_query_params_text,
        })
        return facet_serializer_class(*args, **kwargs)

    def get_facet_serializer_class(self):
        """
        Return the class to use for serializing facets.
        Defaults to using ``self.facet_serializer_class``.
        """
        if self.facet_serializer_class is None:
            raise AttributeError(
                "%(cls)s should either include a `facet_serializer_class` attribute, "
                "or override %(cls)s.get_facet_serializer_class() method." %
                {"cls": self.__class__.__name__}
            )
        return self.facet_serializer_class

    def get_facet_objects_serializer(self, *args, **kwargs):
        """
        Return the serializer instance which should be used for
        serializing faceted objects.
        """
        facet_objects_serializer_class = self.get_facet_objects_serializer_class()
        kwargs["context"] = self.get_serializer_context()
        return facet_objects_serializer_class(*args, **kwargs)

    def get_facet_objects_serializer_class(self):
        """
        Return the class to use for serializing faceted objects.
        Defaults to using the views ``self.serializer_class`` if not
        ``self.facet_objects_serializer_class`` is set.
        """
        return self.facet_objects_serializer_class or super(FacetMixin, self).get_serializer_class()
