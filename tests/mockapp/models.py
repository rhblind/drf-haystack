# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import pytz
from datetime import date, datetime, timedelta
from random import randrange, randint

from django.db import models


def get_random_date(start=date(1950, 1, 1), end=date.today()):
    """
    :return a random date between `start` and `end`
    """
    delta = ((end - start).days * 24 * 60 * 60)
    return start + timedelta(seconds=randrange(delta))


def get_random_datetime(start=datetime(1950, 1, 1, 0, 0), end=datetime.today()):
    """
    :return a random datetime
    """
    delta = ((end - start).total_seconds())
    return (start + timedelta(seconds=randint(0, int(delta)))).replace(tzinfo=pytz.UTC)


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


class MockPerson(models.Model):

    firstname = models.CharField(max_length=20)
    lastname = models.CharField(max_length=20)
    birthdate = models.DateField(null=True, default=get_random_date)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s %s" % (self.firstname, self.lastname)


class MockPet(models.Model):

    name = models.CharField(max_length=20)
    species = models.CharField(max_length=20)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class MockAllField(models.Model):

    charfield = models.CharField(max_length=100)
    integerfield = models.IntegerField()
    floatfield = models.FloatField()
    decimalfield = models.DecimalField(max_digits=5, decimal_places=2)
    boolfield = models.BooleanField(default=False)
    datefield = models.DateField(default=get_random_date)
    datetimefield = models.DateTimeField(default=get_random_datetime)

    def __str__(self):
        return self.charfield
