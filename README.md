Haystack for Django REST Framework
==================================

Build status
------------


About
-----

Small library which tries to simplify integration of Haystack with Django REST Framework.
Fresh [documentation available](http://drf-haystack.readthedocs.org/en/latest/>) on Read the docs!

Supported versions
------------------

- Python 2.7+ and Python 3.4+
- [All supported versions of Django](https://www.djangoproject.com/download/#supported-versions>)
- Haystack 2.4 and above
- Django REST Framework 3.2 and above
    

Installation
------------

    $ pip install drf-haystack

Supported features
------------------
We aim to support most features Haystack does (or at least those which can be used in a REST API).
Currently we support:

- Autocomplete
- Boost (Experimental)
- Faceting
- Geo Spatial Search
- Highlighting
- More Like This
    
Show me more!
-------------

```
from drf_haystack.serializers import HaystackSerializer
from drf_haystack.viewsets import HaystackViewSet

from myapp.search_indexes import PersonIndex  # BYOI™ (Bring Your Own Index)

# Serializer
class PersonSerializer(HaystackSerializer):
    class Meta:
        index_classes = [PersonIndex]
        fields = ["firstname", "lastname", "full_name"]

# ViewSet
class PersonSearchViewSet(HaystackViewSet):
    index_models = [Person]
    serializer_class = PersonSerializer
```

That's it, you're good to go. Hook it up to a DRF router and happy searching!
