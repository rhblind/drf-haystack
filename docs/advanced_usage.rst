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

    Pretty neat =)

