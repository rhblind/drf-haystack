# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import copy
import warnings
from itertools import chain

from django.core.exceptions import ImproperlyConfigured
from django.utils import six

from haystack import fields as haystack_fields
from haystack.query import EmptySearchQuerySet
from haystack.utils import Highlighter

from rest_framework import serializers
from rest_framework.compat import OrderedDict
from rest_framework.fields import (
    BooleanField, CharField, DateField, DateTimeField,
    DecimalField, FloatField, IntegerField, empty
)
from rest_framework.utils.field_mapping import ClassLookupDict, get_field_kwargs


class HaystackSerializer(serializers.Serializer):
    """
    A `HaystackSerializer` which populates fields based on
    which models that are available in the SearchQueryset.
    """
    _field_mapping = ClassLookupDict({
        haystack_fields.BooleanField: BooleanField,
        haystack_fields.CharField: CharField,
        haystack_fields.DateField: DateField,
        haystack_fields.DateTimeField: DateTimeField,
        haystack_fields.DecimalField: DecimalField,
        haystack_fields.EdgeNgramField: CharField,
        haystack_fields.FacetBooleanField: BooleanField,
        haystack_fields.FacetCharField: CharField,
        haystack_fields.FacetDateField: DateField,
        haystack_fields.FacetDateTimeField: DateTimeField,
        haystack_fields.FacetDecimalField: DecimalField,
        haystack_fields.FacetFloatField: FloatField,
        haystack_fields.FacetIntegerField: IntegerField,
        haystack_fields.FacetMultiValueField: CharField,
        haystack_fields.FloatField: FloatField,
        haystack_fields.IntegerField: IntegerField,
        haystack_fields.LocationField: CharField,
        haystack_fields.MultiValueField: CharField,
        haystack_fields.NgramField: CharField,
    })

    def __init__(self, instance=None, data=empty, **kwargs):
        super(HaystackSerializer, self).__init__(instance, data, **kwargs)

        try:
            if not hasattr(self.Meta, "index_classes"):
                raise ImproperlyConfigured("You must set the 'index_classes' attribute "
                                           "on the serializer Meta class.")
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

    def get_fields(self):
        """
        Get the required fields for serializing the result.
        """

        field_mapping = OrderedDict()

        fields = getattr(self.Meta, "fields", [])
        exclude = getattr(self.Meta, "exclude", [])
        ignore_fields = getattr(self.Meta, "ignore_fields", [])

        declared_fields = copy.deepcopy(self._declared_fields)

        if fields and exclude:
            raise ImproperlyConfigured("Cannot set both `fields` and `exclude`.")

        # This has some problems with it. If we're having multiple indexes in
        # the `index_classes` they might have overlapping attribute names. Here
        # we currently only support unique field attributes, and the first one
        # encountered is the only one we'll care about.
        # TODO: Please fix ;)
        for index_cls in self.Meta.index_classes:
            for field_name, field_type in six.iteritems(index_cls.fields):
                if field_name in field_mapping:
                    warnings.warn("Field '%s' is already in the field list with field type "
                                  "'%s'. Will _not_ add the field another time." %
                                  (field_name, field_type.field_type))
                    continue

                if field_name not in fields or field_name in exclude or field_name in ignore_fields:
                    continue

                # Look up the field attributes on the current index model,
                # in order to correctly instantiate the serializer field.
                model = index_cls().get_model()
                kwargs = self._get_default_field_kwargs(model, field_type)
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
        Since we might be dealing with multiple indexes, some fields might
        not be valid for all results. Do not render the fields which don't belong
        to the search result.
        """
        ret = super(HaystackSerializer, self).to_representation(instance)
        for field in self.fields.keys():
            if field not in chain(instance.searchindex.fields.keys(), self._declared_fields.keys()):
                del ret[field]

        if hasattr(instance, "highlighted") and instance.highlighted:
            ret["highlighted"] = instance.highlighted[0]
        return ret


class HighlighterMixin(HaystackSerializer):
    """
    This mixin adds support for highlighting (the pure python, portable
    version, not SearchQuerySet().highlight()). See Haystack docs
    for more info).
    """

    highlighter_class = Highlighter
    highlighter_css_class = "highlighted"
    highlighter_html_tag = "span"
    highlighter_max_length = 200

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
        words = " ".join(six.itervalues(self.context["request"].GET))
        highlighter = self.get_highlighter()(words, **{
            "html_tag": self.highlighter_html_tag,
            "css_class": self.highlighter_css_class,
            "max_length": self.highlighter_max_length
        })
        document_field = self.get_document_field(instance)
        if highlighter and document_field:
            ret["highlighted"] = highlighter.highlight(getattr(instance, document_field))
        return ret
