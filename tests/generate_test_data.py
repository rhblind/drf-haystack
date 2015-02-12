# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os
import json
import random

from datetime import datetime, timedelta

from faker import Factory


if __name__ == "__main__":

    random.seed()
    now = datetime.utcnow()
    fake = Factory.create()

    mock_locations = []

    # Create 100 records
    for i in range(1, 101):
        created = now - timedelta(days=random.randint(6, 36), seconds=random.randint(0, 3600))
        mock_locations.append({
            "id": i,
            "latitude": random.triangular(59.71, 60.11),
            "longitude": random.triangular(10.54, 11.00),
            "address": fake.street_address().replace("?", ""),
            "city": "Oslo",
            "zip_code": "0%4d" % random.randint(1, 1295),
            "created": created.isoformat() + "Z"
        })

    with open(os.path.join(os.path.dirname(__file__), "mockapp", "migrations", "mock_locations.json"), "w") as f:
        f.write(json.dumps(mock_locations))
