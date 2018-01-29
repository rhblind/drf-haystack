# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os
from django.core.exceptions import ImproperlyConfigured

test_runner = None
old_config = None

os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"

import django
if hasattr(django, "setup"):
    django.setup()


def _geospatial_support():
    try:
        import geopy
        from haystack.utils.geo import Point
    except (ImportError, ImproperlyConfigured):
        return False
    else:
        return True
geospatial_support = _geospatial_support()


def _restframework_version():
    import rest_framework
    return tuple(map(int, rest_framework.VERSION.split(".")))
restframework_version = _restframework_version()


def _elasticsearch_version():
    import elasticsearch
    return elasticsearch.VERSION
elasticsearch_version = _elasticsearch_version()


def setup():
    from django.test.runner import DiscoverRunner
    global test_runner
    global old_config

    test_runner = DiscoverRunner()
    test_runner.setup_test_environment()
    old_config = test_runner.setup_databases()


def teardown():
    test_runner.teardown_databases(old_config)
    test_runner.teardown_test_environment()

