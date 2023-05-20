#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import django
from django.core.management import call_command


def start(argv=None):
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"
    django.setup()

    call_command("test", sys.argv[1:])


if __name__ == "__main__":
    start(sys.argv)
