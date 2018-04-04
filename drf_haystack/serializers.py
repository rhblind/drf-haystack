# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import copy
import warnings
from itertools import chain
from datetime import datetime

try:
    from collections import OrderedDict
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict

from django.core.exceptions import ImproperlyConfigured
from django.utils import six

from haystack import fields as haystack_fields
from haystack.query import EmptySearchQuerySet
from haystack.utils import Highlighter

from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.utils.field_mapping import ClassLookupDict, get_field_kwargs

from drf_haystack.fields import (
    HaystackBooleanField, HaystackCharField, HaystackDateField, HaystackDateTimeField,
    HaystackDecimalField, HaystackFloatField, HaystackIntegerField, HaystackMultiValueField,
    FacetDictField, FacetListField
)


class Meta(type):
    """
    Template for the HaystackSerializerMeta.Meta class.
    """

    fields = tuple()
    exclude = tuple()
    search_fields = tuple()
    index_classes = tuple()
    serializers = tuple()
    ignore_fields = tuple()
    field_aliases = {}
    field_options = {}
    index_aliases = {}

    def __new__(mcs, name, bases, attrs):
        cls = super(Meta, mcs).__new__(mcs, str(name), bases, attrs)

        if cls.fields and cls.exclude:
            raise ImproperlyConfigured("%s cannot define both 'fields' and 'exclude'." % name)

        return cls

    def __setattr__(cls, key, value):
        raise AttributeError("Meta class is immutable.")

    def __delattr__(cls, key, value):
        raise AttributeError("Meta class is immutable.")


class HaystackSerializerMeta(serializers.SerializerMetaclass):

    """
    Metaclass for the HaystackSerializer that ensures that all declared subclasses implemented a Meta.
    """

    def __new__(mcs, name, bases, attrs):
        attrs.setdefault("_abstract", False)

        cls = super(HaystackSerializerMeta, mcs).__new__(mcs, str(name), bases, attrs)

        if getattr(cls, "Meta", None):
            cls.Meta = Meta("Meta", (Meta,), dict(cls.Meta.__dict__))

        elif not cls._abstract:
            raise ImproperlyConfigured("%s must implement a Meta class or have the property _abstract" % name)

        return cls


class HaystackSerializer(six.with_metaclass(HaystackSerializerMeta, serializers.Serializer)):
    """
    A `HaystackSerializer` which populates fields based on
    which models that are available in the SearchQueryset.
    """

    _abstract = True

    _field_mapping = ClassLookupDict({
        haystack_fields.BooleanField: HaystackBooleanField,
        haystack_fields.CharField: HaystackCharField,
        haystack_fields.DateField: HaystackDateField,
        haystack_fields.DateTimeField: HaystackDateTimeField,
        haystack_fields.DecimalField: HaystackDecimalField,
        haystack_fields.EdgeNgramField: HaystackCharField,
        haystack_fields.FacetBooleanField: HaystackBooleanField,
        haystack_fields.FacetCharField: HaystackCharField,
        haystack_fields.FacetDateField: HaystackDateField,
        haystack_fields.FacetDateTimeField: HaystackDateTimeField,
        haystack_fields.FacetDecimalField: HaystackDecimalField,
        haystack_fields.FacetFloatField: HaystackFloatField,
        haystack_fields.FacetIntegerField: HaystackIntegerField,
        haystack_fields.FacetMultiValueField: HaystackMultiValueField,
        haystack_fields.FloatField: HaystackFloatField,
        haystack_fields.IntegerField: HaystackIntegerField,
        haystack_fields.LocationField: HaystackCharField,
        haystack_fields.MultiValueField: HaystackMultiValueField,
        haystack_fields.NgramField: HaystackCharField,
    })

    def __init__(self, instance=None, data=empty, **kwargs):
        super(HaystackSerializer, self).__init__(instance, data, **kwargs)

        if not self.Meta.index_classes and not self.Meta.serializers:
            raise ImproperlyConfigured("You must set either the 'index_classes' or 'serializers' "
                                       "attribute on the serializer Meta class.")

        if not self.instance:
            self.instance = EmptySearchQuerySet()

    @staticmethod
    def _get_default_field_kwargs(model, field):
        """
        Get the required attributes from the model field in order
        to instantiate a REST Framework serializer field.
        """
        kwargs = {}
        if field.model_attr in model._meta.get_fields():
            model_field = model._meta.get_field(field.model_attr)[0]
            kwargs = get_field_kwargs(field.model_attr, model_field)

            # Remove stuff we don't care about!
            delete_attrs = [
                "allow_blank",
                "choices",
                "model_field",
            ]
            for attr in delete_attrs:
                if attr in kwargs:
                    del kwargs[attr]

        return kwargs

    def _get_index_field(self, field_name):
        """
        Returns the correct index field.
        """
        return field_name

    def _get_index_class_name(self, index_cls):
        """
        Converts in index model class to a name suitable for use as a field name prefix. A user
        may optionally specify custom aliases via an 'index_aliases' attribute on the Meta class
        """
        cls_name = index_cls.__name__
        aliases = self.Meta.index_aliases
        return aliases.get(cls_name, cls_name.split('.')[-1])

    def get_fields(self):
        """
        Get the required fields for serializing the result.
        """

        fields = self.Meta.fields
        exclude = self.Meta.exclude
        ignore_fields = self.Meta.ignore_fields
        indices = self.Meta.index_classes

        declared_fields = copy.deepcopy(self._declared_fields)
        prefix_field_names = len(indices) > 1
        field_mapping = OrderedDict()

        # overlapping fields on multiple indices is supported by internally prefixing the field
        # names with the index class to which they belong or, optionally, a user-provided alias
        # for the index.
        for index_cls in self.Meta.index_classes:
            prefix = ""
            if prefix_field_names:
                prefix = "_%s__" % self._get_index_class_name(index_cls)
            for field_name, field_type in six.iteritems(index_cls.fields):
                orig_name = field_name
                field_name = "%s%s" % (prefix, field_name)

                # Don't use this field if it is in `ignore_fields`
                if orig_name in ignore_fields or field_name in ignore_fields:
                    continue
                # When fields to include are decided by `exclude`
                if exclude:
                    if orig_name in exclude or field_name in exclude:
                        continue
                # When fields to include are decided by `fields`
                if fields:
                    if orig_name not in fields and field_name not in fields:
                        continue

                # Look up the field attributes on the current index model,
                # in order to correctly instantiate the serializer field.
                model = index_cls().get_model()
                kwargs = self._get_default_field_kwargs(model, field_type)
                kwargs['prefix_field_names'] = prefix_field_names
                field_mapping[field_name] = self._field_mapping[field_type](**kwargs)

        # Add any explicitly declared fields. They *will* override any index fields
        # in case of naming collision!.
        if declared_fields:
            for field_name in declared_fields:
                field_mapping[field_name] = declared_fields[field_name]
        return field_mapping

    def to_representation(self, instance):
        """
        If we have a serializer mapping, use that.  Otherwise, use standard serializer behavior
        Since we might be dealing with multiple indexes, some fields might
        not be valid for all results. Do not render the fields which don't belong
        to the search result.
        """
        if self.Meta.serializers:
            ret = self.multi_serializer_representation(instance)
        else:
            ret = super(HaystackSerializer, self).to_representation(instance)
            prefix_field_names = len(getattr(self.Meta, "index_classes")) > 1
            current_index = self._get_index_class_name(type(instance.searchindex))
            for field in self.fields.keys():
                orig_field = field
                if prefix_field_names:
                    parts = field.split("__")
                    if len(parts) > 1:
                        index = parts[0][1:]  # trim the preceding '_'
                        field = parts[1]
                        if index == current_index:
                            ret[field] = ret[orig_field]
                        del ret[orig_field]
                elif field not in chain(instance.searchindex.fields.keys(), self._declared_fields.keys()):
                    del ret[orig_field]

        # include the highlighted field in either case
        if getattr(instance, "highlighted", None):
            ret["highlighted"] = instance.highlighted[0]
        return ret

    def multi_serializer_representation(self, instance):
        serializers = self.Meta.serializers
        index = instance.searchindex
        serializer_class = serializers.get(type(index), None)
        if not serializer_class:
            raise ImproperlyConfigured("Could not find serializer for %s in mapping" % index)
        return serializer_class(context=self._context).to_representation(instance)


class FacetFieldSerializer(serializers.Serializer):
    """
    Responsible for serializing a faceted result.
    """

    text = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()
    narrow_url = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        self._parent_field = None
        super(FacetFieldSerializer, self).__init__(*args, **kwargs)

    @property
    def parent_field(self):
        return self._parent_field

    @parent_field.setter
    def parent_field(self, value):
        self._parent_field = value

    def get_paginate_by_param(self):
        """
        Returns the ``paginate_by_param`` for the (root) view paginator class.
        This is needed in order to remove the query parameter from faceted
        narrow urls.

        If using a custom pagination class, this class attribute needs to
        be set manually.
        """
        if hasattr(self.root, "paginate_by_param") and self.root.paginate_by_param:
            return self.root.paginate_by_param

        pagination_class = self.context["view"].pagination_class
        if not pagination_class:
            return None

        # PageNumberPagination
        if hasattr(pagination_class, "page_query_param"):
            return pagination_class.page_query_param

        # LimitOffsetPagination
        elif hasattr(pagination_class, "offset_query_param"):
            return pagination_class.offset_query_param

        # CursorPagination
        elif hasattr(pagination_class, "cursor_query_param"):
            return pagination_class.cursor_query_param

        else:
            raise AttributeError(
                "%(root_cls)s is missing a `paginate_by_param` attribute. "
                "Define a %(root_cls)s.paginate_by_param or override "
                "%(cls)s.get_paginate_by_param()." % {
                    "root_cls": self.root.__class__.__name__,
                    "cls": self.__class__.__name__
                })

    def get_text(self, instance):
        """
        Haystack facets are returned as a two-tuple (value, count).
        The text field should contain the faceted value.
        """
        instance = instance[0]
        if isinstance(instance, (six.text_type, six.string_types)):
            return serializers.CharField(read_only=True).to_representation(instance)
        elif isinstance(instance, datetime):
            return serializers.DateTimeField(read_only=True).to_representation(instance)
        return instance

    def get_count(self, instance):
        """
        Haystack facets are returned as a two-tuple (value, count).
        The count field should contain the faceted count.
        """
        instance = instance[1]
        return serializers.IntegerField(read_only=True).to_representation(instance)

    def get_narrow_url(self, instance):
        """
        Return a link suitable for narrowing on the current item.
        """
        text = instance[0]
        request = self.context["request"]
        query_params = request.GET.copy()

        # Never keep the page query parameter in narrowing urls.
        # It will raise a NotFound exception when trying to paginate a narrowed queryset.
        page_query_param = self.get_paginate_by_param()
        if page_query_param and page_query_param in query_params:
            del query_params[page_query_param]

        selected_facets = set(query_params.pop(self.root.facet_query_params_text, []))
        selected_facets.add("%(field)s_exact:%(text)s" % {"field": self.parent_field, "text": text})
        query_params.setlist(self.root.facet_query_params_text, sorted(selected_facets))

        path = "%(path)s?%(query)s" % {"path": request.path_info, "query": query_params.urlencode()}
        url = request.build_absolute_uri(path)
        return serializers.Hyperlink(url, "narrow-url")

    def to_representation(self, field, instance):
        """
        Set the ``parent_field`` property equal to the current field on the serializer class,
        so that each field can query it to see what kind of attribute they are processing.
        """
        self.parent_field = field
        return super(FacetFieldSerializer, self).to_representation(instance)


class HaystackFacetSerializer(six.with_metaclass(HaystackSerializerMeta, serializers.Serializer)):
    """
    The ``HaystackFacetSerializer`` is used to serialize the ``facet_counts()``
    dictionary results on a ``SearchQuerySet`` instance.
    """

    _abstract = True
    serialize_objects = False
    paginate_by_param = None
    facet_dict_field_class = FacetDictField
    facet_list_field_class = FacetListField
    facet_field_serializer_class = FacetFieldSerializer

    def get_fields(self):
        """
        This returns a dictionary containing the top most fields,
        ``dates``, ``fields`` and ``queries``.
        """
        field_mapping = OrderedDict()
        for field, data in self.instance.items():
            field_mapping.update(
                {field: self.facet_dict_field_class(
                    child=self.facet_list_field_class(child=self.facet_field_serializer_class(data)), required=False)}
            )

        if self.serialize_objects is True:
            field_mapping["objects"] = serializers.SerializerMethodField()

        return field_mapping

    def get_objects(self, instance):
        """
        Return a list of objects matching the faceted result.
        """
        view = self.context["view"]
        queryset = self.context["objects"]

        page = view.paginate_queryset(queryset)
        if page is not None:
            serializer = view.get_facet_objects_serializer(page, many=True)
            return OrderedDict([
                ("count", self.get_count(queryset)),
                ("next", view.paginator.get_next_link()),
                ("previous", view.paginator.get_previous_link()),
                ("results", serializer.data)
            ])

        serializer = view.get_serializer(queryset, many=True)
        return serializer.data

    def get_count(self, queryset):
        """
        Determine an object count, supporting either querysets or regular lists.
        """
        try:
            return queryset.count()
        except (AttributeError, TypeError):
            return len(queryset)

    @property
    def facet_query_params_text(self):
        return self.context["facet_query_params_text"]


class HaystackSerializerMixin(object):
    """
    This mixin can be added to a serializer to use the actual object as the data source for serialization rather
    than the data stored in the search index fields.  This makes it easy to return data from search results in
    the same format as elsewhere in your API and reuse your existing serializers
    """

    def to_representation(self, instance):
        obj = instance.object
        return super(HaystackSerializerMixin, self).to_representation(obj)


class HighlighterMixin(object):
    """
    This mixin adds support for ``highlighting`` (the pure python, portable
    version, not SearchQuerySet().highlight()). See Haystack docs
    for more info).
    """

    highlighter_class = Highlighter
    highlighter_css_class = "highlighted"
    highlighter_html_tag = "span"
    highlighter_max_length = 200
    highlighter_field = None

    def get_highlighter(self):
        if not self.highlighter_class:
            raise ImproperlyConfigured(
                "%(cls)s is missing a highlighter_class. Define %(cls)s.highlighter_class, "
                "or override %(cls)s.get_highlighter()." %
                {"cls": self.__class__.__name__}
            )
        return self.highlighter_class

    @staticmethod
    def get_document_field(instance):
        """
        Returns which field the search index has marked as it's
        `document=True` field.
        """
        for name, field in instance.searchindex.fields.items():
            if field.document is True:
                return name

    def to_representation(self, instance):
        ret = super(HighlighterMixin, self).to_representation(instance)
        terms = " ".join(six.itervalues(self.context["request"].GET))
        if terms:
            highlighter = self.get_highlighter()(terms, **{
                "html_tag": self.highlighter_html_tag,
                "css_class": self.highlighter_css_class,
                "max_length": self.highlighter_max_length
            })
            document_field = self.get_document_field(instance)
            if highlighter and document_field:
                ret["highlighted"] = highlighter.highlight(getattr(instance, self.highlighter_field or document_field))
        return ret
