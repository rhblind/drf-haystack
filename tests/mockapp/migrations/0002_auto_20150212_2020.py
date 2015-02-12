# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os
import json
from django.db import models, migrations

cwd = os.path.join(os.path.dirname(__file__))


def load_data(apps, schema_editor):
    with open(os.path.join(cwd, 'mock_locations.json'), 'r') as f:
        model = apps.get_model('mockapp', 'MockLocation')
        model.objects.bulk_create(model(**item) for item in json.loads(f.read()))

    from tests.mockapp.search_indexes import MockLocationIndex
    MockLocationIndex().update()


class Migration(migrations.Migration):

    dependencies = [
        ('mockapp', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_data)
    ]
