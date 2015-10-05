# -*- coding: utf-8 -*-
#
# Unit tests for the `drf_haystack.serializers` classes.
#

from __future__ import absolute_import, unicode_literals

import json
import warnings
from datetime import datetime, timedelta

from django.conf.urls import url, include
from django.core.exceptions import ImproperlyConfigured
from django.http import QueryDict
from django.test import TestCase

from haystack.query import SearchQuerySet

from rest_framework import serializers
from rest_framework.routers import DefaultRouter
from rest_framework.test import APIRequestFactory, APITestCase

from drf_haystack.generics import SQHighlighterMixin
from drf_haystack.serializers import (
    HighlighterMixin, HaystackSerializer,
    HaystackSerializerMixin, HaystackFacetSerializer
)
from drf_haystack.viewsets import HaystackViewSet

from .mixins import WarningTestCaseMixin
from .mockapp.models import MockPerson, MockPet
from .mockapp.search_indexes import MockPersonIndex, MockPetIndex

factory = APIRequestFactory()


class SearchPersonSerializer(HaystackSerializer):
    more_like_this = serializers.HyperlinkedIdentityField(view_name="search-person-more-like-this", read_only=True)

    class Meta:
        index_classes = [MockPersonIndex]
        fields = ["firstname", "lastname", "full_name"]


class SearchPersonFacetSerializer(HaystackFacetSerializer):

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
                "gap_amount": 7
            }
        }


class SearchPersonViewSet(HaystackViewSet):
    serializer_class = SearchPersonSerializer
    facet_serializer_class = SearchPersonFacetSerializer

    class Meta:
        index_models = [MockPerson]


router = DefaultRouter()
router.register("search-person", viewset=SearchPersonViewSet, base_name="search-person")

urlpatterns = [
    url(r"^", include(router.urls))
]


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

        class Serializer5(HaystackSerializer):

            class Meta:
                index_classes = [MockPersonIndex]
                exclude = ["firstname"]

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
        self.serializer5 = Serializer5

        self.view1 = ViewSet1
        self.view2 = ViewSet2

    def tearDown(self):
        MockPersonIndex().clear()

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
            self.assertEqual(str(e), "You must set either the 'index_classes' or 'serializers' "
                                     "attribute on the serializer Meta class.")

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

    def test_serializer_get_fields_with_exclude(self):
        from rest_framework.fields import CharField

        obj = SearchQuerySet().filter(lastname="Foreman")[0]
        serializer = self.serializer5(instance=obj)
        fields = serializer.get_fields()
        assert isinstance(fields, dict), self.fail("serializer.data is not a dict")
        assert isinstance(fields["text"], CharField), self.fail("serializer 'text' field is not a CharField instance")
        assert "firstname" not in fields, self.fail("serializer 'firstname' should not be present")
        assert isinstance(fields["lastname"], CharField), self.fail("serializer 'lastname' field is not a CharField instance")
        assert isinstance(fields["autocomplete"], CharField), self.fail("serializer 'autocomplete' field is not a CharField instance")


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
            _MockPersonIndex__hair_color = serializers.CharField()
            extra = serializers.IntegerField()

            class Meta:
                index_classes = [MockPersonIndex, MockPetIndex]
                exclude = ["firstname"]

            def get__MockPersonIndex__hair_color(self):
                return "black"

            def get_extra(self):
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
        assert len(data) == 4, self.fail("all objects are not present")
        for result in data:
            if "name" in result:
                assert "species" in result, self.fail("Pet results should have 'species' and 'name' fields")
                assert "firstname" not in result, self.fail("Pet results should have 'species' and 'name' fields")
                assert "lastname" not in result, self.fail("Pet results should have 'species' and 'name' fields")
            elif "firstname" in result:
                assert "lastname" in result, self.fail("Person results should have 'firstname' and 'lastname' fields")
                assert "name" not in result, self.fail("Person results should have 'firstname' and 'lastname' fields")
                assert "species" not in result, self.fail("Person results should have 'firstname' and 'lastname' fields")
            else:
                self.fail("Result should contain either Pet or Person fields")

    def test_serializer_multiple_index_declared_fields(self):
        objs = SearchQuerySet().filter(text="John")
        serializer = self.serializer2(instance=objs, many=True)
        data = serializer.data
        assert len(data) == 4, self.fail("all objects are not present")
        for result in data:
            if "name" in result:
                assert "extra" in result, self.fail("'extra' should be present in Pet results")
                assert "hair_color" not in result, self.fail("'hair_color' should not be present in Pet results")
            elif "lastname" in result:
                assert "extra" in result, self.fail("'extra' should be present in Person results")
                assert "hair_color" in result, self.fail("'hair_color' should be present in Person results")
            else:
                self.fail("Result should contain either Pet or Person fields")


class HaystackSerializerHighlighterMixinTestCase(WarningTestCaseMixin, TestCase):

    fixtures = ["mockperson"]

    def setUp(self):
        MockPersonIndex().reindex()

        class Serializer1(HaystackSerializer):
            class Meta:
                index_classes = [MockPersonIndex]
                fields = ["firstname", "lastname", "full_name"]

        class Serializer2(HighlighterMixin, HaystackSerializer):
            highlighter_html_tag = "div"
            highlighter_css_class = "my-fancy-highlighter"
            highlighter_field = "description"

            class Meta:
                index_classes = [MockPersonIndex]
                fields = ["firstname", "lastname", "description"]

        class Serializer3(Serializer2):
            highlighter_class = None

        class ViewSet1(SQHighlighterMixin, HaystackViewSet):
            serializer_class = Serializer1

        class ViewSet2(HaystackViewSet):
            serializer_class = Serializer2

        class ViewSet3(HaystackViewSet):
            serializer_class = Serializer3

        self.viewset1 = ViewSet1
        self.viewset2 = ViewSet2
        self.viewset3 = ViewSet3

    def tearDown(self):
        MockPersonIndex().clear()

    def test_serializer_qs_highlighting(self):
        request = factory.get(path="/", data={"firstname": "jeremy"}, content_type="application/json")
        response = self.viewset1.as_view(actions={"get": "list"})(request)
        response.render()
        for result in json.loads(response.content.decode()):
            self.assertTrue("highlighted" in result)
            self.assertEqual(
                result["highlighted"],
                " ".join(("<em>Jeremy</em>", "%s\n" % result["lastname"]))
            )

    def test_serializer_qs_highlighter_gives_deprecation_warning(self):
        request = factory.get(path="/", data={"firstname": "jeremy"}, content_type="application/json")
        self.assertWarning(DeprecationWarning, self.viewset1.as_view(actions={"get": "list"}), request)

    def test_serializer_highlighting(self):
        request = factory.get(path="/", data={"firstname": "jeremy"}, content_type="application/json")
        response = self.viewset2.as_view(actions={"get": "list"})(request)
        response.render()
        for result in json.loads(response.content.decode()):
            self.assertTrue("highlighted" in result)
            self.assertEqual(
                result["highlighted"],
                " ".join(('<%(tag)s class="%(css_class)s">Jeremy</%(tag)s>' % {
                    "tag": self.viewset2.serializer_class.highlighter_html_tag,
                    "css_class": self.viewset2.serializer_class.highlighter_css_class
                }, "%s" % "is a nice chap!"))
            )

    def test_serializer_highlighter_raise_no_highlighter_class(self):
        request = factory.get(path="/", data={"firstname": "jeremy"}, content_type="application/json")
        try:
            self.viewset3.as_view(actions={"get": "list"})(request)
            self.fail("Did not raise ImproperlyConfigured error when called without a serializer_class")
        except ImproperlyConfigured as e:
            self.assertEqual(
                str(e),
                "%(cls)s is missing a highlighter_class. Define %(cls)s.highlighter_class, "
                "or override %(cls)s.get_highlighter()." % {"cls": self.viewset3.serializer_class.__name__}
            )


class HaystackSerializerMoreLikeThisTestCase(APITestCase):

    fixtures = ["mockperson"]
    urls = "tests.test_serializers"

    def setUp(self):
        MockPersonIndex().reindex()

    def tearDown(self):
        MockPersonIndex().clear()

    def test_serializer_more_like_this_link(self):
        response = self.client.get(
            path="/search-person/",
            data={"firstname": "odysseus", "lastname": "cooley"},
            format="json"
        )
        self.assertEqual(
            response.data,
            [{
                "lastname": "Cooley",
                "full_name": "Odysseus Cooley",
                "firstname": "Odysseus",
                "more_like_this": "http://testserver/search-person/18/more-like-this/"
            }]
        )


class HaystackFacetSerializerTestCase(TestCase):

    fixtures = ["mockperson"]
    urls = "tests.test_serializers"

    def setUp(self):
        MockPersonIndex().reindex()
        self.response = self.client.get(
            path="/search-person/facets/",
            data={},
            format=json
        )

    def tearDown(self):
        MockPersonIndex().clear()

    def test_serializer_facet_top_level_structure(self):
        for key in ("fields", "dates", "queries"):
            self.assertContains(self.response, key, count=1)

    def test_serializer_facet_field_result(self):
        fields = self.response.data["fields"]
        for field in ("firstname", "lastname"):
            self.assertTrue(field in fields)
            self.assertTrue(isinstance(fields[field], list))

        self.assertEqual(len(fields["firstname"]), 88)
        self.assertEqual(len(fields["lastname"]), 97)

        firstname = fields["firstname"][0]
        self.assertTrue([k in firstname for k in ("text", "count", "narrow_url")])
        self.assertEqual(firstname["text"], "John")
        self.assertEqual(firstname["count"], 3)
        self.assertEqual(firstname["narrow_url"], "/search-person/facets/?selected_facets=firstname_exact%3AJohn")

        lastname = fields["lastname"][0]
        self.assertTrue([k in lastname for k in ("text", "count", "narrow_url")])
        self.assertEqual(lastname["text"], "Porter")
        self.assertEqual(lastname["count"], 2)
        self.assertEqual(lastname["narrow_url"], "/search-person/facets/?selected_facets=lastname_exact%3APorter")

    def test_serializer_facet_date_result(self):
        dates = self.response.data["dates"]
        self.assertTrue("created" in dates)
        self.assertTrue([k in dates for k in ("text", "count", "narrow_url")])
        self.assertEqual(len(dates["created"]), 1)

        created = dates["created"][0]
        self.assertEqual(created["text"], "2015-05-01T00:00:00")
        self.assertEqual(created["count"], 100)
        self.assertEqual(created["narrow_url"], "/search-person/facets/?selected_facets=created_exact%3A2015-05-01+00%3A00%3A00")

    def test_serializer_facet_narrow(self):
        response = self.client.get(
            path="/search-person/facets/",
            data=QueryDict("selected_facets=firstname_exact:John&selected_facets=lastname_exact:McClane"),
            format="json"
        )
        self.maxDiff = None

        self.assertEqual(response.data["queries"], {})

        self.assertTrue([all(("firstname", "lastname" in response.data["fields"]))])

        self.assertEqual(len(response.data["fields"]["firstname"]), 1)
        self.assertEqual(response.data["fields"]["firstname"][0]["text"], "John")
        self.assertEqual(response.data["fields"]["firstname"][0]["count"], 1)
        print("firstname: ", response.data["fields"]["firstname"][0]["narrow_url"])
        self.assertEqual(response.data["fields"]["firstname"][0]["narrow_url"], (
            "/search-person/facets/?selected_facets=firstname_exact%3AJohn&selected_facets=lastname_exact%3AMcClane"
        ))

        self.assertEqual(len(response.data["fields"]["lastname"]), 1)
        self.assertEqual(response.data["fields"]["lastname"][0]["text"], "McClane")
        self.assertEqual(response.data["fields"]["lastname"][0]["count"], 1)
        print("lastname: ", response.data["fields"]["lastname"][0]["narrow_url"])
        self.assertEqual(response.data["fields"]["lastname"][0]["narrow_url"], (
            "/search-person/facets/?selected_facets=firstname_exact%3AJohn&selected_facets=lastname_exact%3AMcClane"
        ))

        self.assertTrue("created" in response.data["dates"])
        self.assertEqual(len(response.data["dates"]), 1)
        self.assertEqual(response.data["dates"]["created"][0]["text"], "2015-05-01T00:00:00")
        self.assertEqual(response.data["dates"]["created"][0]["count"], 1)
        print("created: ", response.data["dates"]["created"][0]["narrow_url"])
        self.assertEqual(response.data["dates"]["created"][0]["narrow_url"], (
            "/search-person/facets/?selected_facets=created_exact%3A2015-05-01+00%3A00%3A00"
            "&selected_facets=firstname_exact%3AJohn&selected_facets=lastname_exact%3AMcClane"
        ))


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
                "updated": "2015-05-19T10:48:08.686000Z"
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
