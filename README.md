Haystack for Django REST Framework
==================================

Build status
------------

[![Build Status](https://travis-ci.org/rhblind/drf-haystack.svg?branch=master)](https://travis-ci.org/rhblind/drf-haystack)
[![Coverage Status](https://coveralls.io/repos/github/rhblind/drf-haystack/badge.svg?branch=master)](https://coveralls.io/github/rhblind/drf-haystack?branch=master)
[![PyPI version](https://badge.fury.io/py/drf-haystack.svg)](https://badge.fury.io/py/drf-haystack)
[![Documentation Status](https://readthedocs.org/projects/drf-haystack/badge/?version=latest)](http://drf-haystack.readthedocs.io/en/latest/?badge=latest)


About
-----

Small library which tries to simplify integration of Haystack with Django REST Framework.
Fresh [documentation available](https://drf-haystack.readthedocs.io/en/latest/) on Read the docs!

Supported versions
------------------

- Python 3.7 and above
- Django >=2.2,<4.3
- Haystack 2.8, 3.2
- Django REST Framework >=3.7.0,<3.16
- elasticsearch >=2.0.0,<=8.3.3,


Installation
------------

    $ pip install drf-haystack

Supported features
------------------
We aim to support most features Haystack does (or at least those which can be used in a REST API).
Currently, we support:

- Autocomplete
- Boost (Experimental)
- Faceting
- Geo Spatial Search
- Highlighting
- More Like This

Show me more!
-------------

```python
from drf_haystack.serializers import HaystackSerializer
from drf_haystack.viewsets import HaystackViewSet

from myapp.search_indexes import PersonIndex  # You would define this Index normally as per Haystack's documentation

# Serializer
class PersonSearchSerializer(HaystackSerializer):
    class Meta:
        index_classes = [PersonIndex]
        fields = ["firstname", "lastname", "full_name"]

# ViewSet
class PersonSearchViewSet(HaystackViewSet):
    index_models = [Person]
    serializer_class = PersonSerializer
```

That's it, you're good to go. Hook it up to a DRF router and happy searching!
