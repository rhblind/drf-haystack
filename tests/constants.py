# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os
import json
from django.conf import settings

with open(os.path.join(settings.BASE_DIR, "mockapp", "migrations", "mock_locations.json"), "r") as f:
    size = len(json.loads(f.read()))

DATA_SET_SIZE = size