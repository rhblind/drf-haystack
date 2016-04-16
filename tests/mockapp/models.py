# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from datetime import date, timedelta
from random import randrange

from django.db import models
from django.utils.encoding import python_2_unicode_compatible


def get_random_date(start=date(1950, 1, 1), end=date.today()):
    """
    :return a random date between `start` and `end`
    """
    delta = ((end - start).days * 24 * 60 * 60)
    return start + timedelta(seconds=randrange(delta))


@python_2_unicode_compatible
class MockLocation(models.Model):

    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=30)
    zip_code = models.CharField(max_length=10)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.address

    @property
    def coordinates(self):
        try:
            from haystack.utils.geo import Point
        except ImportError:
            return None
        else:
            return Point(self.longitude, self.latitude, srid=4326)


@python_2_unicode_compatible
class MockPerson(models.Model):

    firstname = models.CharField(max_length=20)
    lastname = models.CharField(max_length=20)
    birthdate = models.DateField(null=True, default=get_random_date)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s %s" % (self.firstname, self.lastname)


@python_2_unicode_compatible
class MockPet(models.Model):

    name = models.CharField(max_length=20)
    species = models.CharField(max_length=20)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
