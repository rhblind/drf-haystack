# -*- coding: utf-8 -*-
#
# Unit tests for the `drf_haystack.serializers` classes.
#

from __future__ import absolute_import, unicode_literals

import json
from datetime import datetime, timedelta

import six
from django.conf.urls import url, include
from django.core.exceptions import ImproperlyConfigured
from django.http import QueryDict
from django.test import TestCase, SimpleTestCase, override_settings
from haystack.query import SearchQuerySet

from rest_framework import serializers
from rest_framework.fields import CharField, IntegerField
from rest_framework.routers import DefaultRouter
from rest_framework.test import APIRequestFactory, APITestCase

from drf_haystack import fields
from drf_haystack.serializers import (
    HighlighterMixin, HaystackSerializer,
    HaystackSerializerMixin, HaystackFacetSerializer,
    HaystackSerializerMeta)
from drf_haystack.viewsets import HaystackViewSet
from drf_haystack.mixins import MoreLikeThisMixin, FacetMixin

from .mixins import WarningTestCaseMixin
from .mockapp.models import MockPerson, MockAllField
from .mockapp.search_indexes import MockPersonIndex, MockPetIndex, MockAllFieldIndex

factory = APIRequestFactory()


# More like this stuff
class SearchPersonMLTSerializer(HaystackSerializer):
    more_like_this = serializers.HyperlinkedIdentityField(view_name="search-person-mlt-more-like-this", read_only=True)

    class Meta:
        index_classes = [MockPersonIndex]
        fields = ["firstname", "lastname", "full_name"]


class SearchPersonMLTViewSet(MoreLikeThisMixin, HaystackViewSet):
    serializer_class = SearchPersonMLTSerializer

    class Meta:
        index_models = [MockPerson]


# Faceting stuff
class SearchPersonFSerializer(HaystackSerializer):

    class Meta:
        index_classes = [MockPersonIndex]
        fields = ["firstname", "lastname", "full_name"]


class SearchPersonFacetSerializer(HaystackFacetSerializer):
    serialize_objects = True

    class Meta:
        index_classes = [MockPersonIndex]
        fields = ["firstname", "lastname", "created"]
        field_options = {
            "firstname": {},
            "lastname": {},
            "created": {
                "start_date": datetime.now() - timedelta(days=10 * 365),
                "end_date": datetime.now(),
                "gap_by": "month",
                "gap_amount": 1
            }
        }


class SearchPersonFacetViewSet(FacetMixin, HaystackViewSet):
    serializer_class = SearchPersonFSerializer
    facet_serializer_class = SearchPersonFacetSerializer

    class Meta:
        index_models = [MockPerson]


router = DefaultRouter()
router.register("search-person-mlt", viewset=SearchPersonMLTViewSet, basename="search-person-mlt")
router.register("search-person-facet", viewset=SearchPersonFacetViewSet, basename="search-person-facet")

urlpatterns = [
    url(r"^", include(router.urls))
]


class HaystackSerializerTestCase(WarningTestCaseMixin, TestCase):

    fixtures = ["mockperson", "mockpet"]

    def setUp(self):
        MockPersonIndex().reindex()
        MockPetIndex().reindex()

        class Serializer1(HaystackSerializer):

            integer_field = serializers.IntegerField()
            city = serializers.SerializerMethodField()

            class Meta:
                index_classes = [MockPersonIndex]
                fields = ["text", "firstname", "lastname", "autocomplete"]

            def get_integer_field(self, instance):
                return 1

            def get_city(self, instance):
                return "Declared overriding field"

        class Serializer2(HaystackSerializer):

            class Meta:
                index_classes = [MockPersonIndex]
                exclude = ["firstname"]

        class Serializer3(HaystackSerializer):

            class Meta:
                index_classes = [MockPersonIndex]
                fields = ["text", "firstname", "lastname", "autocomplete"]
                ignore_fields = ["autocomplete"]

        class Serializer7(HaystackSerializer):

            class Meta:
                index_classes = [MockPetIndex]

        class ViewSet1(HaystackViewSet):
            serializer_class = Serializer1

            class Meta:
                index_models = [MockPerson]

        self.serializer1 = Serializer1
        self.serializer2 = Serializer2
        self.serializer3 = Serializer3
        self.serializer7 = Serializer7
        self.view1 = ViewSet1

    def tearDown(self):
        MockPersonIndex().clear()

    def test_serializer_raise_without_meta_class(self):
        try:
            class Serializer(HaystackSerializer):
                pass
            self.fail("Did not fail when defining a Serializer without a Meta class")
        except ImproperlyConfigured as e:
            self.assertEqual(str(e), "%s must implement a Meta class or have the property _abstract" % "Serializer")

    def test_serializer_gets_default_instance(self):
        serializer = self.serializer1(instance=None)
        self.assertIsInstance(serializer.instance, SearchQuerySet,
                              "Did not get default instance of type SearchQuerySet")

    def test_serializer_get_fields(self):
        obj = SearchQuerySet().filter(lastname="Foreman")[0]
        serializer = self.serializer1(instance=obj)
        fields = serializer.get_fields()

        self.assertIsInstance(fields, dict)
        self.assertIsInstance(fields["integer_field"], IntegerField)
        self.assertIsInstance(fields["text"], CharField)
        self.assertIsInstance(fields["firstname"], CharField)
        self.assertIsInstance(fields["lastname"], CharField)
        self.assertIsInstance(fields["autocomplete"], CharField)

    def test_serializer_get_fields_with_exclude(self):
        obj = SearchQuerySet().filter(lastname="Foreman")[0]
        serializer = self.serializer2(instance=obj)
        fields = serializer.get_fields()

        self.assertIsInstance(fields, dict)
        self.assertIsInstance(fields["text"], CharField)
        self.assertIsInstance(fields["lastname"], CharField)
        self.assertIsInstance(fields["autocomplete"], CharField)
        self.assertFalse("firstname" in fields)

    def test_serializer_get_fields_with_ignore_fields(self):
        obj = SearchQuerySet().filter(lastname="Foreman")[0]
        serializer = self.serializer3(instance=obj)
        fields = serializer.get_fields()

        self.assertIsInstance(fields, dict)
        self.assertIsInstance(fields["text"], CharField)
        self.assertIsInstance(fields["firstname"], CharField)
        self.assertIsInstance(fields["lastname"], CharField)
        self.assertFalse("autocomplete" in fields)

    def test_serializer_boolean_field(self):
        dog = self.serializer7(instance=SearchQuerySet().filter(species="Dog")[0])
        iguana = self.serializer7(instance=SearchQuerySet().filter(species="Iguana")[0])
        self.assertTrue(dog.data["has_rabies"])
        self.assertFalse(iguana.data["has_rabies"])

    def test_serializer_declared_field_overrides(self):
        obj = SearchQuerySet().filter(lastname="Foreman")[0]
        serializer = self.serializer1(instance=obj)

        self.assertEqual(serializer.data['city'], "Declared overriding field")


class HaystackSerializerAllFieldsTestCase(TestCase):

    fixtures = ["mockallfield"]

    def setUp(self):
        MockAllFieldIndex().reindex()

        class Serializer1(HaystackSerializer):
            class Meta:
                index_classes = [MockAllFieldIndex]
                fields = ["charfield", "integerfield", "floatfield",
                          "decimalfield", "boolfield", "datefield",
                          "datetimefield", "multivaluefield"]

        self.serializer1 = Serializer1

    def test_serialize_field_is_correct_type(self):
        obj = SearchQuerySet().models(MockAllField).latest('datetimefield')
        serializer = self.serializer1(instance=obj, many=False)

        self.assertIsInstance(serializer.fields['charfield'], fields.HaystackCharField)
        self.assertIsInstance(serializer.fields['integerfield'], fields.HaystackIntegerField)
        self.assertIsInstance(serializer.fields['floatfield'], fields.HaystackFloatField)
        self.assertIsInstance(serializer.fields['decimalfield'], fields.HaystackDecimalField)
        self.assertIsInstance(serializer.fields['boolfield'], fields.HaystackBooleanField)
        self.assertIsInstance(serializer.fields['datefield'], fields.HaystackDateField)
        self.assertIsInstance(serializer.fields['datetimefield'], fields.HaystackDateTimeField)
        self.assertIsInstance(serializer.fields['multivaluefield'], fields.HaystackMultiValueField)


class HaystackSerializerMultipleIndexTestCase(WarningTestCaseMixin, TestCase):

    fixtures = ["mockperson", "mockpet"]

    def setUp(self):
        MockPersonIndex().reindex()
        MockPetIndex().reindex()

        class Serializer1(HaystackSerializer):
            """
            Regular multiple index serializer
            """

            class Meta:
                index_classes = [MockPersonIndex, MockPetIndex]
                fields = ["text", "firstname", "lastname", "name", "species", "autocomplete"]

        class Serializer2(HaystackSerializer):
            """
            Multiple index serializer with declared fields
            """
            _MockPersonIndex__hair_color = serializers.SerializerMethodField()
            extra = serializers.SerializerMethodField()

            class Meta:
                index_classes = [MockPersonIndex, MockPetIndex]
                exclude = ["firstname"]

            def get__MockPersonIndex__hair_color(self, instance):
                return "black"

            def get_extra(self, instance):
                return 1

        class Serializer3(HaystackSerializer):
            """
            Multiple index serializer with index aliases
            """

            class Meta:
                index_classes = [MockPersonIndex, MockPetIndex]
                exclude = ["firstname"]
                index_aliases = {
                    'mockapp.MockPersonIndex': 'People'
                }

        class ViewSet1(HaystackViewSet):
            serializer_class = Serializer1

        class ViewSet2(HaystackViewSet):
            serializer_class = Serializer2

        class ViewSet3(HaystackViewSet):
            serializer_class = Serializer3

        self.serializer1 = Serializer1
        self.serializer2 = Serializer2
        self.serializer3 = Serializer3

        self.view1 = ViewSet1
        self.view2 = ViewSet2
        self.view3 = ViewSet3

    def tearDown(self):
        MockPersonIndex().clear()
        MockPetIndex().clear()

    def test_serializer_multiple_index_data(self):
        objs = SearchQuerySet().filter(text="John")
        serializer = self.serializer1(instance=objs, many=True)
        data = serializer.data

        self.assertEqual(len(data), 4)
        for result in data:
            if "name" in result:
                self.assertTrue("species" in result, "Pet results should have 'species' and 'name' fields")
                self.assertTrue("firstname" not in result, "Pet results should have 'species' and 'name' fields")
                self.assertTrue("lastname" not in result, "Pet results should have 'species' and 'name' fields")
            elif "firstname" in result:
                self.assertTrue("lastname" in result, "Person results should have 'firstname' and 'lastname' fields")
                self.assertTrue("name" not in result, "Person results should have 'firstname' and 'lastname' fields")
                self.assertTrue("species" not in result, "Person results should have 'firstname' and 'lastname' fields")
            else:
                self.fail("Result should contain either Pet or Person fields")

    def test_serializer_multiple_index_declared_fields(self):
        objs = SearchQuerySet().filter(text="John")
        serializer = self.serializer2(instance=objs, many=True)
        data = serializer.data

        self.assertEqual(len(data), 4)
        for result in data:
            if "name" in result:
                self.assertTrue("extra" in result, "'extra' should be present in Pet results")
                self.assertEqual(result["extra"], 1, "The value of 'extra' should be 1")
                self.assertTrue("hair_color" not in result, "'hair_color' should not be present in Pet results")
            elif "lastname" in result:
                self.assertTrue("extra" in result, "'extra' should be present in Person results")
                self.assertEqual(result["extra"], 1, "The value of 'extra' should be 1")
                self.assertTrue("hair_color" in result, "'hair_color' should be present in Person results")
                self.assertEqual(result["hair_color"], "black", "The value of 'hair_color' should be 'black'")
            else:
                self.fail("Result should contain either Pet or Person fields")


class HaystackSerializerHighlighterMixinTestCase(WarningTestCaseMixin, TestCase):

    fixtures = ["mockperson"]

    def setUp(self):
        MockPersonIndex().reindex()

        class Serializer2(HighlighterMixin, HaystackSerializer):
            highlighter_html_tag = "div"
            highlighter_css_class = "my-fancy-highlighter"
            highlighter_field = "description"

            class Meta:
                index_classes = [MockPersonIndex]
                fields = ["firstname", "lastname", "description"]

        class Serializer3(Serializer2):
            highlighter_class = None

        class ViewSet1(HaystackViewSet):
            serializer_class = Serializer2

        class ViewSet2(HaystackViewSet):
            serializer_class = Serializer3

        self.view1 = ViewSet1
        self.view2 = ViewSet2

    def tearDown(self):
        MockPersonIndex().clear()

    def test_serializer_highlighting(self):
        request = factory.get(path="/", data={"firstname": "jeremy"}, content_type="application/json")
        response = self.view1.as_view(actions={"get": "list"})(request)
        response.render()
        for result in json.loads(response.content.decode()):
            self.assertTrue("highlighted" in result)
            self.assertEqual(
                result["highlighted"],
                " ".join(('<%(tag)s class="%(css_class)s">Jeremy</%(tag)s>' % {
                    "tag": self.view1.serializer_class.highlighter_html_tag,
                    "css_class": self.view1.serializer_class.highlighter_css_class
                }, "%s" % "is a nice chap!"))
            )

    def test_serializer_highlighter_raise_no_highlighter_class(self):
        request = factory.get(path="/", data={"firstname": "jeremy"}, content_type="application/json")
        try:
            self.view2.as_view(actions={"get": "list"})(request)
            self.fail("Did not raise ImproperlyConfigured error when called without a serializer_class")
        except ImproperlyConfigured as e:
            self.assertEqual(
                str(e),
                "%(cls)s is missing a highlighter_class. Define %(cls)s.highlighter_class, "
                "or override %(cls)s.get_highlighter()." % {"cls": self.view2.serializer_class.__name__}
            )


@override_settings(ROOT_URLCONF="tests.test_serializers")
class HaystackSerializerMoreLikeThisTestCase(APITestCase):

    fixtures = ["mockperson"]

    def setUp(self):
        MockPersonIndex().reindex()

    def tearDown(self):
        MockPersonIndex().clear()

    def test_serializer_more_like_this_link(self):
        response = self.client.get(
            path="/search-person-mlt/",
            data={"firstname": "odysseus", "lastname": "cooley"},
            format="json"
        )
        self.assertEqual(
            response.data,
            [{
                "lastname": "Cooley",
                "full_name": "Odysseus Cooley",
                "firstname": "Odysseus",
                "more_like_this": "http://testserver/search-person-mlt/18/more-like-this/"
            }]
        )


@override_settings(ROOT_URLCONF="tests.test_serializers")
class HaystackFacetSerializerTestCase(TestCase):

    fixtures = ["mockperson"]

    def setUp(self):
        MockPersonIndex().reindex()
        self.response = self.client.get(
            path="/search-person-facet/facets/",
            data={},
            format="json"
        )

    def tearDown(self):
        MockPersonIndex().clear()

    @staticmethod
    def build_absolute_uri(location):
        """
        Builds an absolute URI using the test server's domain and the specified location.
        """
        location = location.lstrip("/")
        return "http://testserver/{location}".format(location=location)

    @staticmethod
    def is_paginated_facet_response(response):
        """
        Returns True if the response.data seems like a faceted result.
        Only works for responses created with the test client.
        """
        return "objects" in response.data and \
               all([k in response.data["objects"] for k in ("count", "next", "previous", "results")])

    def test_serializer_facet_top_level_structure(self):
        for key in ("fields", "dates", "queries"):
            self.assertContains(self.response, key, count=1)

    def test_serializer_facet_field_result(self):
        fields = self.response.data["fields"]
        for field in ("firstname", "lastname"):
            self.assertTrue(field in fields)
            self.assertTrue(isinstance(fields[field], list))

        firstname = fields["firstname"][0]
        self.assertTrue({"text", "count", "narrow_url"} <= set(firstname))
        self.assertEqual(
            firstname["narrow_url"],
            self.build_absolute_uri("/search-person-facet/facets/?selected_facets=firstname_exact%3A{term}".format(
                term=firstname["text"]))
        )

        lastname = fields["lastname"][0]
        self.assertTrue({"text", "count", "narrow_url"} <= set(lastname))
        self.assertEqual(
            lastname["narrow_url"],
            self.build_absolute_uri("/search-person-facet/facets/?selected_facets=lastname_exact%3A{term}".format(
                term=lastname["text"]
            ))
        )

    def test_serializer_facet_date_result(self):
        dates = self.response.data["dates"]
        self.assertTrue("created" in dates)
        self.assertEqual(len(dates["created"]), 1)

        created = dates["created"][0]
        self.assertTrue(all([k in created for k in ("text", "count", "narrow_url")]))
        self.assertEqual(created["text"], "2015-05-01T00:00:00Z")
        self.assertEqual(created["count"], 100)
        self.assertEqual(
            created["narrow_url"],
            self.build_absolute_uri("/search-person-facet/facets/?selected_facets=created_exact%3A2015-05-01+00%3A00%3A00")
        )

    def test_serializer_facet_queries_result(self):
        # Not Implemented
        pass

    def test_serializer_facet_narrow(self):
        response = self.client.get(
            path="/search-person-facet/facets/",
            data=QueryDict("selected_facets=firstname_exact:John&selected_facets=lastname_exact:McClane"),
            format="json"
        )
        self.assertEqual(response.data["queries"], {})

        self.assertTrue([all(("firstname", "lastname" in response.data["fields"]))])

        self.assertEqual(len(response.data["fields"]["firstname"]), 1)
        self.assertEqual(response.data["fields"]["firstname"][0]["text"], "John")
        self.assertEqual(response.data["fields"]["firstname"][0]["count"], 1)
        self.assertEqual(
            response.data["fields"]["firstname"][0]["narrow_url"],
            self.build_absolute_uri("/search-person-facet/facets/?selected_facets=firstname_exact%3AJohn"
                                    "&selected_facets=lastname_exact%3AMcClane")
        )

        self.assertEqual(len(response.data["fields"]["lastname"]), 1)
        self.assertEqual(response.data["fields"]["lastname"][0]["text"], "McClane")
        self.assertEqual(response.data["fields"]["lastname"][0]["count"], 1)
        self.assertEqual(
            response.data["fields"]["lastname"][0]["narrow_url"],
            self.build_absolute_uri("/search-person-facet/facets/?selected_facets=firstname_exact%3AJohn"
                                    "&selected_facets=lastname_exact%3AMcClane")
        )

        self.assertTrue("created" in response.data["dates"])
        self.assertEqual(len(response.data["dates"]), 1)
        self.assertEqual(response.data["dates"]["created"][0]["text"], "2015-05-01T00:00:00Z")
        self.assertEqual(response.data["dates"]["created"][0]["count"], 1)
        self.assertEqual(
            response.data["dates"]["created"][0]["narrow_url"],
            self.build_absolute_uri("/search-person-facet/facets/?selected_facets=created_exact%3A2015-05-01+00%3A00%3A00"
                                    "&selected_facets=firstname_exact%3AJohn&selected_facets=lastname_exact%3AMcClane"
                                    )
        )

    def test_serializer_raise_without_meta_class(self):
        try:
            class FacetSerializer(HaystackFacetSerializer):
                pass
            self.fail("Did not fail when defining a Serializer without a Meta class")
        except ImproperlyConfigured as e:
            self.assertEqual(str(e), "%s must implement a Meta class or have the property _abstract" % "FacetSerializer")


class HaystackSerializerMixinTestCase(WarningTestCaseMixin, TestCase):

    fixtures = ["mockperson"]

    def setUp(self):
        MockPersonIndex().reindex()

        class MockPersonSerializer(serializers.ModelSerializer):
            class Meta:
                model = MockPerson
                fields = ('id', 'firstname', 'lastname', 'created', 'updated')
                read_only_fields = ('created', 'updated')

        class Serializer1(HaystackSerializerMixin, MockPersonSerializer):
            class Meta(MockPersonSerializer.Meta):
                search_fields = ['text', ]

        class Viewset1(HaystackViewSet):
            serializer_class = Serializer1

        self.serializer1 = Serializer1
        self.viewset1 = Viewset1

    def tearDown(self):
        MockPersonIndex().clear()

    def test_serializer_mixin(self):
        objs = SearchQuerySet().filter(text="Foreman")
        serializer = self.serializer1(instance=objs, many=True)
        self.assertEqual(
            json.loads(json.dumps(serializer.data)),
            [{
                "id": 1,
                "firstname": "Abel",
                "lastname": "Foreman",
                "created": "2015-05-19T10:48:08.686000Z",
                "updated": "2016-04-24T16:02:59.378000Z"
            }]
        )


class HaystackMultiSerializerTestCase(WarningTestCaseMixin, TestCase):

    fixtures = ["mockperson", "mockpet"]

    def setUp(self):
        MockPersonIndex().reindex()
        MockPetIndex().reindex()

        class MockPersonSerializer(HaystackSerializer):
            class Meta:
                index_classes = [MockPersonIndex]
                fields = ('text', 'firstname', 'lastname', 'description')

        class MockPetSerializer(HaystackSerializer):
            class Meta:
                index_classes = [MockPetIndex]
                exclude = ('description', 'autocomplete')

        class Serializer1(HaystackSerializer):
            class Meta:
                serializers = {
                    MockPersonIndex: MockPersonSerializer,
                    MockPetIndex: MockPetSerializer
                }

        self.serializer1 = Serializer1

    def tearDown(self):
        MockPersonIndex().clear()
        MockPetIndex().clear()

    def test_multi_serializer(self):
        objs = SearchQuerySet().filter(text="Zane")
        serializer = self.serializer1(instance=objs, many=True)
        self.assertEqual(
            json.loads(json.dumps(serializer.data)),
            [{
                "has_rabies": True,
                "text": "Zane",
                "name": "Zane",
                "species": "Dog"
            },
            {
                "text": "Zane Griffith\n",
                "firstname": "Zane",
                "lastname": "Griffith",
                "description": "Zane is a nice chap!"
            }]
        )


class TestHaystackSerializerMeta(SimpleTestCase):

    def test_abstract_not_inherited(self):
        class Base(six.with_metaclass(HaystackSerializerMeta, serializers.Serializer)):
            _abstract = True

        def create_subclass():
            class Sub(HaystackSerializer):
                pass

        self.assertRaises(ImproperlyConfigured, create_subclass)


class TestMeta(SimpleTestCase):

    def test_inheritance(self):
        """
        Tests that Meta fields are correctly overriden by subclasses.
        """
        class Serializer(HaystackSerializer):
            class Meta:
                fields = ('overriden_fields',)

        self.assertEqual(Serializer.Meta.fields, ('overriden_fields',))

    def test_default_attrs(self):
        class Serializer(HaystackSerializer):
            class Meta:
                fields = ('overriden_fields',)

        self.assertEqual(Serializer.Meta.exclude, tuple())

    def test_raises_if_fields_and_exclude_defined(self):
        def create_subclass():
            class Serializer(HaystackSerializer):
                class Meta:
                    fields = ('include_field',)
                    exclude = ('exclude_field',)
            return Serializer

        self.assertRaises(ImproperlyConfigured, create_subclass)
