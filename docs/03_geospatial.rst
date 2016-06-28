.. _geospatial-label:

GEO spatial locations
=====================

Some search backends support geo spatial searching. In order to take advantage of this we
have the ``HaystackGEOSpatialFilter``.

.. class:: drf_haystack.filters.HaystackGEOSpatialFilter

.. note::

    The ``HaystackGEOSpatialFilter`` depends on ``geopy`` and ``libgeos``. Make sure to install these
    libraries in order to use this filter.

    .. code-block:: none

        $ pip install geopy
        $ apt-get install libgeos (for debian based linux distros)
          or
        $ brew install geos (for homebrew on OS X)

The geospatial filter is somewhat special, and for the time being, relies on a few assumptions.

#. The index model **must** to have a ``LocationField`` named ``coordinates`` (See :ref:`search-index-example-label` for example). If your ``LocationField`` is named differently, instead of using the ``HaystackGEOSpatialFilter``, subclass the ``BaseHaystackGEOSpatialFilter`` and provide the name of your ``LocationField`` in ``point_field`` (string).
#. The query **must** contain a ``unit`` parameter where the unit is a valid ``UNIT`` in the ``django.contrib.gis.measure.Distance`` class.
#. The query **must** contain a ``from`` parameter which is a comma separated longitude and latitude value.


**Example Geospatial view**

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
        filter_backends = [HaystackGEOSpatialFilter]


**Example subclassing the ``BaseHaystackGEOSpatialFilter``**

Assuming that your ``LocationField`` is named ``location``.

.. code-block:: python

    from drf_haystack.filters import BaseHaystackGEOSpatialFilter

    class CustomHaystackGEOSpatialFilter(BaseHaystackGEOSpatialFilter):
        point_field = 'location'


    class LocationGeoSearchViewSet(HaystackViewSet):

        index_models = [Location]
        serializer_class = LocationSerializer
        filter_backends = [CustomHaystackGEOSpatialFilter]

Assuming the above code works as it should, we would be able to do queries like this:

.. code-block:: none

    /api/v1/search/?zip_code=0351&km=10&from=59.744076,10.152045


The above query would return all entries with zip_code 0351 within 10 kilometers
from the location with latitude 59.744076 and longitude 10.152045.
