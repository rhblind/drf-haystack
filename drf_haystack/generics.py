# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.utils import six

from haystack.backends import SQ
from haystack.query import SearchQuerySet
from rest_framework.generics import GenericAPIView

from drf_haystack.filters import HaystackFilter


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

    # If set to False, DB lookups are done on a per-object basis,
    # resulting in in many individual trips to the database. If True,
    # the SearchQuerySet will group similar objects into a single query.
    load_all = False

    filter_backends = [HaystackFilter]

    def get_queryset(self, index_models=[]):
        """
        Get the list of items for this view.
        Returns ``self.queryset`` if defined and is a ``self.object_class``
        instance.

        @:param index_models: override `self.index_models`
        """
        if self.queryset is not None and isinstance(self.queryset, self.object_class):
            queryset = self.queryset.all()
        else:
            queryset = self.object_class()._clone()
            if len(index_models):
                queryset = queryset.models(*index_models)
            elif len(self.index_models):
                queryset = queryset.models(*self.index_models)
        return queryset

    def get_object(self):
        """
        Fetch a single document from the data store according to whatever
        unique identifier is available for that document in the
        SearchIndex.

        In cases where the view has multiple ``index_models``, add a ``model`` query
        parameter containing a single `app_label.model` name to the request in order
        to override which model to include in the SearchQuerySet.

        Example:
            /api/v1/search/42/?model=myapp.person
        """
        queryset = self.get_queryset()
        if "model" in self.request.query_params:
            try:
                app_label, model = map(six.text_type.lower, self.request.query_params["model"].split(".", 1))
                ctype = ContentType.objects.get(app_label=app_label, model=model)
                queryset = self.get_queryset(index_models=[ctype.model_class()])
            except (ValueError, ContentType.DoesNotExist):
                raise Http404("Could not find any models matching '%s'. Make sure to use a valid "
                              "'app_label.model' name for the 'model' query parameter." % self.request.query_params["model"])

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if lookup_url_kwarg not in self.kwargs:
            raise AttributeError(
                "Expected view %s to be called with a URL keyword argument "
                "named '%s'. Fix your URL conf, or set the `.lookup_field` "
                "attribute on the view correctly." % (self.__class__.__name__, lookup_url_kwarg)
            )
        queryset = queryset.filter(self.query_object((self.document_uid_field, self.kwargs[lookup_url_kwarg])))
        count = queryset.count()
        if count == 1:
            return queryset[0]
        elif count > 1:
            raise Http404("Multiple results matches the given query. Expected a single result.")

        raise Http404("No result matches the given query.")

    def filter_queryset(self, queryset):
        queryset = super(HaystackGenericAPIView, self).filter_queryset(queryset)
        
        if self.load_all:
            queryset = queryset.load_all()

        return queryset
