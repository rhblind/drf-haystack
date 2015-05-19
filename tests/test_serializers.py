# -*- coding: utf-8 -*-
#
# Unit tests for the `drf_haystack.serializers` classes.
#

from __future__ import absolute_import, unicode_literals

import warnings

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from haystack.query import SearchQuerySet
from rest_framework import serializers
from rest_framework.test import APIRequestFactory

from drf_haystack.serializers import HaystackSerializer
from drf_haystack.viewsets import HaystackViewSet

from .mockapp.models import MockPerson
from .mockapp.search_indexes import MockPersonIndex

factory = APIRequestFactory()


class WarningTestCaseMixin(object):
    """
    TestCase mixin to catch warnings
    """

    def assertWarning(self, warning, callable, *args, **kwargs):
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter(action="always")
            callable(*args, **kwargs)
            self.assertTrue(any(item.category == "warning" for item in warning_list))


class HaystackSerializerTestCase(WarningTestCaseMixin, TestCase):

    fixtures = ["mockperson"]

    def setUp(self):

        MockPersonIndex().reindex()

        class Serializer1(HaystackSerializer):
            # This is not allowed. Serializer must implement a
            # `Meta` class
            pass

        class Serializer2(HaystackSerializer):

            class Meta:
                # This is not allowed. The Meta class must implement
                # a `index_classes` attribute
                pass

        class Serializer3(HaystackSerializer):

            class Meta:
                index_classes = [MockPersonIndex]
                fields = ["some_field"]
                exclude = ["another_field"]
                # This is not allowed. Can't set both `fields` and `exclude`

        class Serializer4(HaystackSerializer):

            integer_field = serializers.IntegerField()
            city = serializers.CharField()

            class Meta:
                index_classes = [MockPersonIndex]
                fields = ["text", "firstname", "lastname", "autocomplete"]

            def get_integer_field(self, obj):
                return 1

            def get_city(self, obj):
                return "Declared overriding field"

        class ViewSet1(HaystackViewSet):
            serializer_class = Serializer3

        class ViewSet2(HaystackViewSet):
            serializer_class = Serializer4

            class Meta:
                index_models = [MockPerson]

        self.serializer1 = Serializer1
        self.serializer2 = Serializer2
        self.serializer3 = Serializer3
        self.serializer4 = Serializer4

        self.view1 = ViewSet1
        self.view2 = ViewSet2

    def test_serializer_raise_without_meta_class(self):
        try:
            self.serializer1()
            self.fail("Did not fail when initialized serializer with no Meta class")
        except ImproperlyConfigured as e:
            self.assertEqual(str(e), "%s must implement a Meta class." % self.serializer1.__name__)

    def test_serializer_raise_without_index_models(self):
        try:
            self.serializer2()
            self.fail("Did not fail when initialized serializer with no 'index_classes' attribute")
        except ImproperlyConfigured as e:
            self.assertEqual(str(e), "You must set the 'index_classes' attribute "
                                     "on the serializer Meta class.")

    def test_serializer_raise_on_both_fields_and_exclude(self):
        # Make sure we're getting an ImproperlyConfigured when trying to call a viewset
        # which has both `fields` and `exclude` set.
        request = factory.get(path="/", data="", content_type="application/json")
        try:
            self.view1.as_view(actions={"get": "list"})(request)
            self.fail("Did not fail when serializer has both 'fields' and 'exclude' attributes")
        except ImproperlyConfigured as e:
            self.assertEqual(str(e), "Cannot set both `fields` and `exclude`.")

    def test_serializer_gets_default_instance(self):
        serializer = self.serializer4(instance=None)
        assert isinstance(serializer.instance, SearchQuerySet), self.fail("Did not get default instance "
                                                                          "of type SearchQuerySet")

    def test_serializer_get_fields(self):
        from rest_framework.fields import CharField, IntegerField

        obj = SearchQuerySet().filter(lastname="Foreman")[0]
        serializer = self.serializer4(instance=obj)
        fields = serializer.get_fields()
        assert isinstance(fields, dict), self.fail("serializer.data is not a dict")
        assert isinstance(fields["integer_field"], IntegerField), self.fail("serializer 'integer_field' field is not a IntegerField instance")
        assert isinstance(fields["text"], CharField), self.fail("serializer 'text' field is not a CharField instance")
        assert isinstance(fields["firstname"], CharField), self.fail("serializer 'firstname' field is not a CharField instance")
        assert isinstance(fields["lastname"], CharField), self.fail("serializer 'lastname' field is not a CharField instance")
        assert isinstance(fields["autocomplete"], CharField), self.fail("serializer 'autocomplete' field is not a CharField instance")
