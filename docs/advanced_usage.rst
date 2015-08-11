.. _advanced-usage-label:

==============
Advanced Usage
==============

Make sure you've read through the :ref:`basic-usage-label`.


Autocomplete
============

Some kind of data such as ie. cities and zip codes could be useful to autocomplete.
We have a Django REST Framework filter for performing autocomplete queries. It works
quite like the regular ``HaystackFilter`` but *must* be run against an ``NgramField`` or
``EdgeNgramField`` in order to work properly. The main difference is that while the
HaystackFilter performs a bitwise ``OR`` on terms for the same parameters, the
``HaystackAutocompleteFilter`` reduce query parameters down to a single filter
(using an ``SQ`` object), and performs a bitwise ``AND``.

.. class:: drf_haystack.filters.HaystackAutocompleteFilter

By adding a list or tuple of ``ignore_fields`` to the serializer's Meta class,
we can tell the REST framework to ignore these fields. This is handy in cases,
where you do not want to serialize and transfer the content of a text, or n-gram
index down to the client.

An example using the autocomplete filter might look something like this.


.. code-block:: python

    class AutocompleteSerializer(HaystackSerializer):

        class Meta:
            index_classes = [LocationIndex]
            fields = ["address", "city", "zip_code", "autocomplete"]
            ignore_fields = ["autocomplete"]

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

#. The index model **must** to have a ``LocationField`` named ``coordinates`` (See :ref:`search-index-example-label` for example).
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


.. note::

    The highlighter will always use the ``document=True`` field on your index to hightlight on.
    See examples below.

SearchQuerySet Highlighting
---------------------------

In order to add support for ``SearchQuerySet().highlight()``, all you have to do is to add the
``HaystackHighlightFilter`` to the ``filter_backends`` in your view. The ``HaystackSerializer`` will
check if your queryset has highlighting enabled, and render an additional ``highlighted`` field to
your result. The highlighted words will be encapsulated in an ``<em>words go here</em>`` html tag.

.. warning::

    The ``SQHighlighterMixin()`` is deprecated in favor of the  ``HaystackHighlightFilter()`` filter backend.

.. class:: drf_haystack.filters.HaystackHighlightFilter


**Example view with highlighting enabled**

.. code-block:: python

    from drf_haystack.viewsets import HaystackViewSet
    from drf_haystack.filters import HaystackHighlightFilter

    from .models import Person
    from .serializers import PersonSerializer


    class SearchViewSet(HaystackViewSet):
        index_models = [Person]
        serializer_class = PersonSerializer
        filter_backends = [HaystackHighlightFilter]


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

This implementation make use of the haystack ``Highlighter()`` class.
It is implemented as a mixin class, and must be applied on the ``Serializer``.
This is somewhat slower, but more configurable than the ``SQHighlighterMixin()``.

.. class:: drf_haystack.serializers.HighlighterMixin

The Highlighter class will be initialized with the following default options, but can be overridden by
changing any of the following class attributes.

    .. code-block:: python

        highlighter_class = Highlighter
        highlighter_css_class = "highlighted"
        highlighter_html_tag = "span"
        highlighter_max_length = 200
        highlighter_field = None

The Highlighter class will usually highlight the ``document_field`` (the field marked ``document=True`` on your
search index class), but this may be overridden by changing the ``highlighter_field``.

You can of course also use your own ``Highlighter`` class by overriding the ``highlighter_class = MyFancyHighLighter``
class attribute.


**Example serializer with highlighter support**

.. code-block:: python

    from drf_haystack.serializers import HighlighterMixin, HaystackSerializer

    class PersonSerializer(HighlighterMixin, HaystackSerializer):

        highlighter_css_class = "my-highlighter-class"
        highlighter_html_tag = "em"

        class Meta:
            index_classes = [PersonIndex]
            fields = ["firstname", "lastname", "full_name"]


Response

.. code-block:: json

    [
        {
            "full_name": "Jeremy Rowland",
            "lastname": "Rowland",
            "firstname": "Jeremy",
            "highlighted": "<em class=\"my-highlighter-class\">Jeremy</em> Rowland\nCreated: May 19, 2015, 10:48 a.m.\nLast modified: May 19, 2015, 10:48 a.m.\n"
        },
        {
            "full_name": "Jeremy Fowler",
            "lastname": "Fowler",
            "firstname": "Jeremy",
            "highlighted": "<em class=\"my-highlighter-class\">Jeremy</em> Fowler\nCreated: May 19, 2015, 10:48 a.m.\nLast modified: May 19, 2015, 10:48 a.m.\n"
        }
    ]


More Like This
==============

Some search backends supports ``More Like This`` features. In order to take advantage of this,
the ``HaystackViewSet`` includes a ``more-like-this`` detail route which is appended to the base name of the
ViewSet. Lets say you have a router which looks like this:

.. code-block:: python

    router = routers.DefaultRouter()
    router.register("search", viewset=SearchViewSet, base_name="search")  # MLT name will be 'search-more-like-this'.

    urlpatterns = patterns(
        "",
        url(r"^", include(router.urls))
    )

The important thing here is that the ``SearchViewSet`` class inherits from the ``HaystackViewSet`` class
in order to get the ``more-like-this`` route automatically added. The view name will be
``{base_name}-more-like-this``, which in this case would be for example ``search-more-like-this``.


Serializing the More Like This URL
----------------------------------

In order to include the ``more-like-this`` url in your result you only have to add a ``HyperlinkedIdentityField``
to your serializer.
Something like this should work okay.

**Example serializer with More Like This**

.. code-block:: python

    class SearchSerializer(HaystackSerializer):

        more_like_this = serializers.HyperlinkedIdentityField(view_name="search-more-like-this", read_only=True)

        class Meta:
            index_classes = [PersonIndex]
            fields = ["firstname", "lastname", "full_name"]


Now, every result you render with this serializer will include a ``more_like_this`` field containing the url
for similar results.

Example response

.. code-block:: json

    [
        {
            "full_name": "Jeremy Rowland",
            "lastname": "Rowland",
            "firstname": "Jeremy",
            "more_like_this": "http://example.com/search/5/more-like-this/"
        }
    ]


Term Boost
==========

Term boost is achieved on the SearchQuerySet level by calling ``SearchQuerySet().boost()``. It is
implemented as a filter backend, and applies boost **after** regular filtering has occurred.

.. class:: drf_haystack.filters.HaystackBoostFilter

.. code-block:: python

    from drf_haystack.filters import HaystackBoostFilter

    class SearchViewSet(HaystackViewSet):
        ...
        filter_backends = [HaystackBoostFilter]


The filter expects the query string to contain a ``boost`` parameter, which is a comma separated string
of the term to boost and the boost value. The boost value must be either an integer or float value.

**Example query**

.. code-block:: none

    /api/v1/search/?firstname=robin&boost=hood,1.1

The query above will first filter on ``firstname=robin`` and next apply a slight boost on any document containing
the word ``hood``.

.. note::

    Term boost are only applied on terms existing in the ``document field``.


.. _permission-classes-label:

Permission Classes
==================

Django REST Framework allows setting certain ``permission_classes`` in order to control access to views.
The generic ``HaystackGenericAPIView`` defaults to ``rest_framework.permissions.AllowAny`` which enforce no
restrictions on the views. This can be overridden on a per-view basis as you would normally do in a regular
`REST Framework APIView <http://www.django-rest-framework.org/api-guide/permissions/#setting-the-permission-policy>`_.


.. note::

    Since we have no Django model or queryset, the following permission classes are *not* supported:

        - ``rest_framework.permissions.DjangoModelPermissions``
        - ``rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly``
        - ``rest_framework.permissions.DjangoObjectPermissions``

    ``POST``, ``PUT``, ``PATCH`` and ``DELETE`` are not supported since Haystack Views
    are read-only. So if you are using the ``rest_framework.permissions.IsAuthenticatedOrReadOnly``
    , this will act just as the ``AllowAny`` permission.


**Example overriding permission classes**

.. code-block:: python

    ...
    from rest_framework.permissions import IsAuthenticated

    class SearchViewSet(HaystackViewSet):
        ...
        permission_classes = [IsAuthenticated]


