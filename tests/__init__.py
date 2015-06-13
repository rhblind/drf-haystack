# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os

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
    except ImportError:
        return False
    else:
        return True
geospatial_support = _geospatial_support()


def setup():
    global test_runner
    global old_config

    try:
        from django.test.runner import DiscoverRunner
        test_runner = DiscoverRunner()
    except ImportError:
        # Django 1.5 did not have the DiscoverRunner
        from django.test.simple import DjangoTestSuiteRunner
        test_runner = DjangoTestSuiteRunner()

    test_runner.setup_test_environment()
    old_config = test_runner.setup_databases()


def teardown():
    test_runner.teardown_databases(old_config)
    test_runner.teardown_test_environment()


