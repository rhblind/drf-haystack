# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import copy
import warnings
from itertools import chain
from datetime import datetime

from django.core.exceptions import ImproperlyConfigured
from django.utils import six
from django.utils.six.moves.urllib import parse as urlparse

from haystack import fields as haystack_fields
from haystack.query import EmptySearchQuerySet
from haystack.utils import Highlighter

from rest_framework import serializers
from rest_framework.compat import OrderedDict
from rest_framework.fields import empty, SkipField
from rest_framework.utils.field_mapping import ClassLookupDict, get_field_kwargs

from .fields import (
    HaystackBooleanField, HaystackCharField, HaystackDateField, HaystackDateTimeField,
    HaystackDecimalField, HaystackFloatField, HaystackIntegerField
)


class HaystackSerializer(serializers.Serializer):
    """
    A `HaystackSerializer` which populates fields based on
    which models that are available in the SearchQueryset.
    """
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
        haystack_fields.FacetMultiValueField: HaystackCharField,
        haystack_fields.FloatField: HaystackFloatField,
        haystack_fields.IntegerField: HaystackIntegerField,
        haystack_fields.LocationField: HaystackCharField,
        haystack_fields.MultiValueField: HaystackCharField,
        haystack_fields.NgramField: HaystackCharField,
    })

    def __init__(self, instance=None, data=empty, **kwargs):
        super(HaystackSerializer, self).__init__(instance, data, **kwargs)

        try:
            if not hasattr(self.Meta, "index_classes") and not hasattr(self.Meta, "serializers"):
                raise ImproperlyConfigured("You must set either the 'index_classes' or 'serializers' "
                                           "attribute on the serializer Meta class.")
        except AttributeError:
            raise ImproperlyConfigured("%s must implement a Meta class." % self.__class__.__name__)

        if not self.instance:
            self.instance = EmptySearchQuerySet()

    @staticmethod
    def _get_default_field_kwargs(model, field):
        """
        Get the required attributes from the model field in order
        to instantiate a REST Framework serializer field.
        """
        kwargs = {}
        if field.model_attr in model._meta.get_all_field_names():
            model_field = model._meta.get_field_by_name(field.model_attr)[0]
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
        aliases = getattr(self.Meta, "index_aliases", {})
        return aliases.get(cls_name, cls_name.split('.')[-1])

    def get_fields(self):
        """
        Get the required fields for serializing the result.
        """

        fields = getattr(self.Meta, "fields", [])
        exclude = getattr(self.Meta, "exclude", [])

        if fields and exclude:
            raise ImproperlyConfigured("Cannot set both `fields` and `exclude`.")

        ignore_fields = getattr(self.Meta, "ignore_fields", [])
        indices = getattr(self.Meta, "index_classes")

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

                # This has become a little more complex, but provides convenient flexibility for users
                if not exclude:
                    if orig_name not in fields and field_name not in fields:
                        continue
                elif orig_name in exclude or field_name in exclude or orig_name in ignore_fields or field_name in ignore_fields:
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
                if field_name in field_mapping:
                    warnings.warn("Field '{field}' already exists in the field list. This *will* "
                                  "overwrite existing field '{field}'".format(field=field_name))
                field_mapping[field_name] = declared_fields[field_name]
        return field_mapping

    def to_representation(self, instance):
        """
        If we have a serializer mapping, use that.  Otherwise, use standard serializer behavior
        Since we might be dealing with multiple indexes, some fields might
        not be valid for all results. Do not render the fields which don't belong
        to the search result.
        """
        if getattr(self.Meta, "serializers", None):
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


class HaystackFacetSerializer(serializers.Serializer):
    """
    The ``HaystackFacetSerializer`` is used to serialize the ``facet_counts()``
    dictionary results on a ``SearchQuerySet`` instance.
    """

    def __init__(self, *args, **kwargs):
        super(HaystackFacetSerializer, self).__init__(*args, **kwargs)

        class FacetDictField(serializers.DictField):
            """
            A special DictField which passes the key attribute down to the children's
            ``to_representation()`` in order to let the serializer know what field they're
            currently processing.
            """
            def to_representation(self, value):
                return dict([
                    (six.text_type(key), self.child.to_representation(key, val))
                    for key, val in value.items()
                ])

        class FacetListField(serializers.ListField):
            """
            The ``FacetListField`` just pass along the key derived from
            ``FacetDictField``.
            """
            def to_representation(self, key, data):
                return [self.child.to_representation(key, item) for item in data]

        class FacetFieldSerializer(serializers.Serializer):
            """
            Responsible for serializing each faceted result.
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

                Since we don't have any means of getting the ``view name`` from here,
                we can only return relative paths.
                """
                text = instance[0]
                query_params = self.context["request"].GET.copy()

                selected_facets = set(query_params.pop("selected_facets", []))
                selected_facets.add("%(field)s_exact:%(text)s" % {"field": self.parent_field, "text": text})
                query_params.setlist("selected_facets", sorted(selected_facets))

                return serializers.Hyperlink("%(path)s?%(query)s" % {
                    "path": self.context["request"].path_info,
                    "query": query_params.urlencode()
                }, name="narrow-url")

            def to_representation(self, field, instance):
                """
                Set the ``parent_field`` property equal to the current field on the serializer class,
                so that each field can query it to see what kind of attribute they are processing.
                """
                self.parent_field = field
                return super(FacetFieldSerializer, self).to_representation(instance)

        self.FacetDictField = FacetDictField
        self.FacetListField = FacetListField
        self.FacetFieldSerializer = FacetFieldSerializer

    def get_fields(self):
        """
        This returns a dictionary containing the top most fields,
        ``dates``, ``fields`` and ``queries``.
        """

        field_mapping = OrderedDict()
        for field, data in self.instance.items():
            field_mapping.update(
                {field: self.FacetDictField(
                    child=self.FacetListField(child=self.FacetFieldSerializer(data)), required=False)}
            )
        return field_mapping


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
