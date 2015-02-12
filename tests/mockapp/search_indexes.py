# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from django.utils import timezone
from haystack import indexes

from .models import MockLocation


class MockLocationIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
    address = indexes.CharField(model_attr="address")
    city = indexes.CharField(model_attr="city")
    zip_code = indexes.CharField(model_attr="zip_code")

    autocomplete = indexes.EdgeNgramField()
    coordinates = indexes.LocationField(model_attr="coordinates")

    @staticmethod
    def prepare_autocomplete(obj):
        return " ".join((
            obj.address, obj.city, obj.zip_code
        ))

    def get_model(self):
        return MockLocation

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(
            created__lte=timezone.now()
        )