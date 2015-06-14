.. _advanced-usage-label:

==============
Advanced Usage
==============

Make sure you've read through the :ref:`basic-usage-label`.


Autocomplete
============

Some kind of data such as ie. cities and zip codes could be useful to autocomplete.
We have a Django REST Framework filter for performing autocomplete queries. It works
quite like the regular `HaystackFilter` but *must* be run against an `NgramField` or
`EdgeNgramField` in order to work properly. The main difference is that while the
HaystackFilter performs a bitwise `OR` on terms for the same parameters, the
`HaystackAutocompleteFilter` reduce query parameters down to a single filter
(using an `SQ` object), and performs a bitwise `AND`.

.. class:: drf_haystack.filters.HaystackAutocompleteFilter


An example using the autocomplete filter might look something like this.


.. code-block:: python

    class AutocompleteSerializer(HaystackSerializer):

        class Meta:
            index_classes = [LocationIndex]
            fields = ["address", "city", "zip_code", "autocomplete"]

            # The `field_aliases` attribute can be used in order to alias a
            # query parameter to a field attribute. In this case a query like
            # /search/?q=oslo would alias the `q` parameter to the `autocomplete`
            # field on the index.
            field_aliases = {
                "q": "autocomplete"
            }

    class AutocompleteSearchViewSet(HaystackViewSet):

        index_models = [Location]
        serializer_class = AutocompleteSerializer
        filter_backends = [HaystackAutocompleteFilter]


GEO Locations
=============

Some search backends support geo spatial searching. In order to take advantage of this we
have the `HaystackGEOSpatialFilter`.

.. class:: drf_haystack.filters.HaystackGEOSpatialFilter

.. warning::

    The `HaystackGEOSpatialFilter` depends on `geopy` and `libgeos`. Make sure to install these
    libraries in order to use this filter.

    .. code-block:: none

        $ pip install geopy
        $ apt-get install libgeos (for debian based linux distros)
          or
        $ brew install geos (for homebrew on OS X)

The geospatial filter is somewhat special, and for the time being, relies on a few assumptions.

#. The index model **must** to have a `LocationField` named `coordinates` (See :ref:`search-index-example-label` for example).
#. The query **must** contain a "unit" parameter where the unit is a valid `UNIT` in the `django.contrib.gis.measure.Distance` class.
#. The query **must** contain a "from" parameter which is a comma separated longitude and latitude value.


Example Geospatial view

.. code-block:: python

    class DistanceSerializer(serializers.Serializer):
        m = serializers.FloatField()
        km = serializers.FloatField()


    class LocationSerializer(HaystackSerializer):

        distance = SerializerMethodField()

        class Meta:
            index_classes = [LocationIndex]
            fields = ["address", "city", "zip_code", "location"]

        def get_distance(self, obj):
            if hasattr(obj, "distance"):
                return DistanceSerializer(obj.distance, many=False).data


    class LocationGeoSearchViewSet(HaystackViewSet):

        index_models = [Location]
        serializer_class = LocationSerializer
        filter_backends = [HaystackFilter, HaystackGEOSpatialFilter]


Assuming the above code works as it should, we would be able to do queries like this:

.. code-block:: none

    /api/v1/search/?zip_code=0351&km=10&from=59.744076,10.152045


The above query would return all entries with zip_code 0351 within 10 kilometers
from the location with latitude 59.744076 and longitude 10.152045.


Highlighting
============

Haystack supports two kind of `Highlighting <https://django-haystack.readthedocs.org/en/latest/highlighting.html>`_,
and we support them both.

#. SearchQuerySet highlighting. This kind of highlighting requires a search backend which has support for
   highlighting, such as Elasticsearch or Solr.
#. Pure python highlighting. This implementation is somewhat slower, but enables highlighting support
   even if your search backend does not support it.


SearchQuerySet Highlighting
---------------------------

In order to add support for `SearchQuerySet().highlight()`, all you have to do is to add a `Mixin class` to
your view. The `HaystackSerializer` will check if your queryset has highlighting enabled, and render an additional
`highlighted` field to your result. The highlighted words will be encapsulated in an `<em>words go here</em>`
html tag.

.. class:: drf_haystack.generics.SQHighlighterMixin


Example view with highlighting enabled

.. code-block:: python

    from drf_haystack.viewsets import HaystackViewSet
    from drf_haystack.generics import SQHighlighterMixin

    from .models import Person
    from .serializers import PersonSerializer


    class SearchViewSet(SQHighlighterMixin, HaystackViewSet):
        index_models = [Person]
        serializer_class = PersonSerializer


Given a query like below

.. code-block:: none

    /api/v1/search/?firstname=jeremy


We would get a result like this

.. code-block:: json

    [
        {
            "lastname": "Rowland",
            "full_name": "Jeremy Rowland",
            "firstname": "Jeremy",
            "highlighted": "<em>Jeremy</em> Rowland\nCreated: May 19, 2015, 10:48 a.m.\nLast modified: May 19, 2015, 10:48 a.m.\n"
        },
        {
            "lastname": "Fowler",
            "full_name": "Jeremy Fowler",
            "firstname": "Jeremy",
            "highlighted": "<em>Jeremy</em> Fowler\nCreated: May 19, 2015, 10:48 a.m.\nLast modified: May 19, 2015, 10:48 a.m.\n"
        }
    ]



Pure Python Highlighting
------------------------

.. todo::

    Write me!
