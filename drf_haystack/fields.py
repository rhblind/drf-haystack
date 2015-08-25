# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from rest_framework.fields import (
    BooleanField, CharField, DateField, DateTimeField,
    DecimalField, FloatField, IntegerField
)


class DRFHaystackFieldMixin(object):
    prefix_field_names = False

    def __init__(self, **kwargs):
        self.prefix_field_names = kwargs.pop('prefix_field_names', False)
        super(DRFHaystackFieldMixin, self).__init__(**kwargs)

    def bind(self, field_name, parent):
        """
        Initializes the field name and parent for the field instance.
        Called when a field is added to the parent serializer instance.
        Taken from DRF and modified to support drf_haystack multiple index
        functionality.
        """

        # In order to enforce a consistent style, we error if a redundant
        # 'source' argument has been used. For example:
        # my_field = serializer.CharField(source='my_field')
        assert self.source != field_name, (
            "It is redundant to specify `source='%s'` on field '%s' in "
            "serializer '%s', because it is the same as the field name. "
            "Remove the `source` keyword argument." %
            (field_name, self.__class__.__name__, parent.__class__.__name__)
        )

        self.field_name = field_name
        self.parent = parent

        # `self.label` should default to being based on the field name.
        if self.label is None:
            self.label = field_name.replace('_', ' ').capitalize()

        # self.source should default to being the same as the field name.
        if self.source is None:
            self.source = self.convert_field_name(field_name)

        # self.source_attrs is a list of attributes that need to be looked up
        # when serializing the instance, or populating the validated data.
        if self.source == '*':
            self.source_attrs = []
        else:
            self.source_attrs = self.source.split('.')

    def convert_field_name(self, field_name):
        if not self.prefix_field_names:
            return field_name
        return field_name.split("__")[-1]


class HaystackBooleanField(DRFHaystackFieldMixin, BooleanField):
    pass


class HaystackCharField(DRFHaystackFieldMixin, CharField):
    pass


class HaystackDateField(DRFHaystackFieldMixin, DateField):
    pass


class HaystackDateTimeField(DRFHaystackFieldMixin, DateTimeField):
    pass


class HaystackDecimalField(DRFHaystackFieldMixin, DecimalField):
    pass


class HaystackFloatField(DRFHaystackFieldMixin, FloatField):
    pass


class HaystackIntegerField(DRFHaystackFieldMixin, IntegerField):
    pass
