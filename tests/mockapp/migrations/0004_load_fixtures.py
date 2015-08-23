# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.core import serializers
from django.db import models, migrations


def load_data(apps, schema_editor):
    """
    Load fixtures for MockPerson, MockPet and MockLocation
    """

    fixtures = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, "fixtures"))

    with open(os.path.join(fixtures, "mockperson.json"), "r") as fixture:
        objects = serializers.deserialize("json", fixture, ignorenonexistent=True)
        for obj in objects:
            obj.save()

    with open(os.path.join(fixtures, "mocklocation.json"), "r") as fixture:
        objects = serializers.deserialize("json", fixture, ignorenonexistent=True)
        for obj in objects:
            obj.save()

    with open(os.path.join(fixtures, "mockpet.json"), "r") as fixture:
        objects = serializers.deserialize("json", fixture, ignorenonexistent=True)
        for obj in objects:
            obj.save()

def unload_data(apps, schema_editor):
    """
    Unload fixtures for MockPerson, MockPet and MockLocation
    """

    MockPerson = apps.get_model("mockapp", "MockPerson")
    MockLocation = apps.get_model("mockapp", "MockLocation")
    MockPet = apps.get_model("mockapp", "MockPet")

    MockPerson.objects.all().delete()
    MockLocation.objects.all().delete()
    MockPet.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("mockapp", "0001_initial"),
        ("mockapp", "0002_mockperson"),
        ("mockapp", "0003_mockpet"),
    ]

    operations = [
        migrations.RunPython(load_data, reverse_code=unload_data)
    ]
