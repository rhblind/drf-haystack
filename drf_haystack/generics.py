# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from haystack.backends import SQ
from haystack.query import SearchQuerySet
from rest_framework.generics import GenericAPIView

from .filters import HaystackFilter


class HaystackGenericAPIView(GenericAPIView):
    """
    Base class for all haystack generic views.
    """
    # Use `index_models` to filter on which search index models we
    # should include in the search result.
    index_models = []

    object_class = SearchQuerySet
    query_object = SQ

    # Override document_uid_field with whatever field in your index
    # you use to uniquely identify a single document. This value will be
    # used wherever the view references the `lookup_field` kwarg.
    document_uid_field = "id"
    lookup_sep = ","

    #
    # REST Framework overrides
    #
    filter_backends = [HaystackFilter]

    def get_queryset(self):
        """
        Get the list of items for this view.
        Returns `self.queryset` if defined and is a `self.object_class`
        instance.
        """
        if self.queryset and isinstance(self.queryset, self.object_class):
            queryset = self.queryset.all()
        else:
            queryset = self.object_class()._clone()
            if len(self.index_models):
                queryset = queryset.models(*self.index_models)
        return queryset

    def get_object(self):
        """
        Fetch a single document from the data store according to whatever
        unique identifier is available for that document in the
        SearchIndex.
        """
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if lookup_url_kwarg not in self.kwargs:
            raise AttributeError(
                "Expected view %s to be called with a URL keyword argument "
                "named '%s'. Fix your URL conf, or set the `.lookup_field` "
                "attribute on the view correctly." % (self.__class__.__name__, lookup_url_kwarg)
            )
        queryset = queryset.filter(self.query_object((self.document_uid_field, self.kwargs[lookup_url_kwarg])))
        if queryset:
            return queryset[0]

        return queryset
