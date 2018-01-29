# -*- coding: utf-8 -*-
#
# Unit tests for the `drf_haystack.viewsets` classes.
#

from __future__ import absolute_import, unicode_literals

import json
from unittest import skipIf

from django.test import TestCase
from django.contrib.auth.models import User

from haystack.query import SearchQuerySet

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.routers import SimpleRouter
from rest_framework.serializers import Serializer
from rest_framework.test import force_authenticate, APIRequestFactory

from drf_haystack.viewsets import HaystackViewSet
from drf_haystack.serializers import HaystackSerializer, HaystackFacetSerializer
from drf_haystack.mixins import MoreLikeThisMixin, FacetMixin

from . import restframework_version
from .mockapp.models import MockPerson, MockPet
from .mockapp.search_indexes import MockPersonIndex, MockPetIndex


factory = APIRequestFactory()


class HaystackViewSetTestCase(TestCase):

    fixtures = ["mockperson", "mockpet"]

    def setUp(self):
        MockPersonIndex().reindex()
        MockPetIndex().reindex()
        self.router = SimpleRouter()

        class FacetSerializer(HaystackFacetSerializer):

            class Meta:
                fields = ["firstname", "lastname", "created"]

        class ViewSet1(FacetMixin, HaystackViewSet):
            index_models = [MockPerson]
            serializer_class = Serializer
            facet_serializer_class = FacetSerializer

        class ViewSet2(MoreLikeThisMixin, HaystackViewSet):
            index_models = [MockPerson]
            serializer_class = Serializer

        class ViewSet3(HaystackViewSet):
            index_models = [MockPerson, MockPet]
            serializer_class = Serializer

        self.view1 = ViewSet1
        self.view2 = ViewSet2
        self.view3 = ViewSet3

    def tearDown(self):
        MockPersonIndex().clear()

    def test_viewset_get_queryset_no_queryset(self):
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view1.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewset_get_queryset_with_queryset(self):
        setattr(self.view1, "queryset", SearchQuerySet().all())
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view1.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewset_get_object_single_index(self):
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view1.as_view(actions={"get": "retrieve"})(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewset_get_object_multiple_indices(self):
        request = factory.get(path="/", data={"model": "mockapp.mockperson"}, content_type="application/json")
        response = self.view3.as_view(actions={"get": "retrieve"})(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewset_get_object_multiple_indices_no_model_query_param(self):
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view3.as_view(actions={"get": "retrieve"})(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_viewset_get_object_multiple_indices_invalid_modelname(self):
        request = factory.get(path="/", data={"model": "spam"}, content_type="application/json")
        response = self.view3.as_view(actions={"get": "retrieve"})(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_viewset_get_obj_raise_404(self):
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view1.as_view(actions={"get": "retrieve"})(request, pk=100000)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_viewset_get_object_invalid_lookup_field(self):
        request = factory.get(path="/", data="", content_type="application/json")
        self.assertRaises(
            AttributeError,
            self.view1.as_view(actions={"get": "retrieve"}), request, invalid_lookup=1
        )

    def test_viewset_get_obj_override_lookup_field(self):
        setattr(self.view1, "lookup_field", "custom_lookup")
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view1.as_view(actions={"get": "retrieve"})(request, custom_lookup=1)
        setattr(self.view1, "lookup_field", "pk")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewset_more_like_this_decorator(self):
        route = self.router.get_routes(self.view2)[2:].pop()
        self.assertEqual(route.url, "^{prefix}/{lookup}/more-like-this{trailing_slash}$")
        self.assertEqual(route.mapping, {"get": "more_like_this"})

    def test_viewset_more_like_this_action_route(self):
        request = factory.get(path="/", data={}, content_type="application/json")
        response = self.view2.as_view(actions={"get": "more_like_this"})(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewset_facets_action_route(self):
        request = factory.get(path="/", data={}, content_type="application/json")
        response = self.view1.as_view(actions={"get": "facets"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class HaystackViewSetPermissionsTestCase(TestCase):

    fixtures = ["mockperson"]

    def setUp(self):
        MockPersonIndex().reindex()

        class ViewSet(HaystackViewSet):
            serializer_class = Serializer

        self.view = ViewSet
        self.user = User.objects.create_user(username="user", email="user@example.com", password="user")
        self.admin_user = User.objects.create_superuser(username="admin", email="admin@example.com", password="admin")

    def tearDown(self):
        MockPersonIndex().clear()

    def test_viewset_get_queryset_with_no_permsission(self):
        setattr(self.view, "permission_classes", [])

        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewset_get_queryset_with_AllowAny_permission(self):
        from rest_framework.permissions import AllowAny
        setattr(self.view, "permission_classes", (AllowAny, ))

        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewset_get_queryset_with_IsAuthenticated_permission(self):
        from rest_framework.permissions import IsAuthenticated
        setattr(self.view, "permission_classes", (IsAuthenticated, ))

        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        force_authenticate(request, user=self.user)
        response = self.view.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewset_get_queryset_with_IsAdminUser_permission(self):
        from rest_framework.permissions import IsAdminUser
        setattr(self.view, "permission_classes", (IsAdminUser,))

        request = factory.get(path="/", data="", content_type="application/json")
        force_authenticate(request, user=self.user)
        response = self.view.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        force_authenticate(request, user=self.admin_user)
        response = self.view.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewset_get_queryset_with_IsAuthenticatedOrReadOnly_permission(self):
        from rest_framework.permissions import IsAuthenticatedOrReadOnly
        setattr(self.view, "permission_classes", (IsAuthenticatedOrReadOnly,))

        # Unauthenticated GET requests should pass
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated GET requests should pass
        request = factory.get(path="/", data="", content_type="application/json")
        force_authenticate(request, user=self.user)
        response = self.view.as_view(actions={"get": "list"})(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # POST, PUT, PATCH and DELETE requests are not supported, so they will
        # raise an error. No need to test the permission.

    @skipIf(not restframework_version < (3, 7), "Skipped due to fix in django-rest-framework > 3.6")
    def test_viewset_get_queryset_with_DjangoModelPermissions_permission(self):
        from rest_framework.permissions import DjangoModelPermissions
        setattr(self.view, "permission_classes", (DjangoModelPermissions,))

        # The `DjangoModelPermissions` is not supported and should raise an
        # AssertionError from rest_framework.permissions.
        request = factory.get(path="/", data="", content_type="application/json")
        try:
            self.view.as_view(actions={"get": "list"})(request)
            self.fail("Did not fail with AssertionError or AttributeError "
                      "when calling HaystackView with DjangoModelPermissions")
        except (AttributeError, AssertionError) as e:
            if isinstance(e, AttributeError):
                self.assertEqual(str(e), "'SearchQuerySet' object has no attribute 'model'")
            else:
                self.assertEqual(str(e), "Cannot apply DjangoModelPermissions on a view that does "
                                         "not have `.model` or `.queryset` property.")

    def test_viewset_get_queryset_with_DjangoModelPermissionsOrAnonReadOnly_permission(self):
        from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
        setattr(self.view, "permission_classes", (DjangoModelPermissionsOrAnonReadOnly,))

        # The `DjangoModelPermissionsOrAnonReadOnly` is not supported and should raise an
        # AssertionError from rest_framework.permissions.
        request = factory.get(path="/", data="", content_type="application/json")
        try:
            self.view.as_view(actions={"get": "list"})(request)
            self.fail("Did not fail with AssertionError when calling HaystackView "
                      "with DjangoModelPermissionsOrAnonReadOnly")
        except (AttributeError, AssertionError) as e:
            if isinstance(e, AttributeError):
                self.assertEqual(str(e), "'SearchQuerySet' object has no attribute 'model'")
            else:
                self.assertEqual(str(e), "Cannot apply DjangoModelPermissions on a view that does "
                                         "not have `.model` or `.queryset` property.")

    @skipIf(not restframework_version < (3, 7), "Skipped due to fix in django-rest-framework > 3.6")
    def test_viewset_get_queryset_with_DjangoObjectPermissions_permission(self):
        from rest_framework.permissions import DjangoObjectPermissions
        setattr(self.view, "permission_classes", (DjangoObjectPermissions,))

        # The `DjangoObjectPermissions` is a subclass of `DjangoModelPermissions` and
        # therefore unsupported.
        request = factory.get(path="/", data="", content_type="application/json")
        try:
            self.view.as_view(actions={"get": "list"})(request)
            self.fail("Did not fail with AssertionError when calling HaystackView with DjangoModelPermissions")
        except (AttributeError, AssertionError) as e:
            if isinstance(e, AttributeError):
                self.assertEqual(str(e), "'SearchQuerySet' object has no attribute 'model'")
            else:
                self.assertEqual(str(e), "Cannot apply DjangoModelPermissions on a view that does "
                                         "not have `.model` or `.queryset` property.")


class PaginatedHaystackViewSetTestCase(TestCase):

    fixtures = ["mockperson"]

    def setUp(self):

        MockPersonIndex().reindex()

        class Serializer1(HaystackSerializer):

            class Meta:
                fields = ["firstname", "lastname"]
                index_classes = [MockPersonIndex]

        class NumberPagination(PageNumberPagination):

            page_size = 5

        class ViewSet1(HaystackViewSet):

            index_models = [MockPerson]
            serializer_class = Serializer1
            pagination_class = NumberPagination

        self.view1 = ViewSet1

    def tearDown(self):
        MockPersonIndex().clear()

    def test_viewset_PageNumberPagination_results(self):
        request = factory.get(path="/", data="", content_type="application/json")
        response = self.view1.as_view(actions={"get": "list"})(request)
        response.render()
        content = json.loads(response.content.decode())

        self.assertTrue(all(k in content for k in ("count", "next", "previous", "results")))
        self.assertEqual(len(content["results"]), 5)

    def test_viewset_PageNumberPagination_navigation_urls(self):
        request = factory.get(path="/", data={"page": 2}, content_type="application/json")
        response = self.view1.as_view(actions={"get": "list"})(request)
        response.render()
        content = json.loads(response.content.decode())

        self.assertEqual(content["previous"], "http://testserver/")
        self.assertEqual(content["next"], "http://testserver/?page=3")
