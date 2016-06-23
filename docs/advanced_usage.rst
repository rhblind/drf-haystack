.. _advanced-usage-label:

==============
Advanced Usage
==============

Make sure you've read through the :ref:`basic-usage-label`.


Query Field Lookups
===================

You can also use field lookups in your field queries. See the
Haystack `field lookups <https://django-haystack.readthedocs.io/en/latest/searchqueryset_api.html?highlight=lookups#id1>`_
documentation for info on what lookups are available.  A query using a lookup might look like the
following:

.. code-block:: none

    http://example.com/api/v1/location/search/?city__startswith=Os

This would perform a query looking up all documents where the `city field` started with "Os".
You might get "Oslo", "Osaka", and "Ostrava".

Query Term Negation
-------------------
You can also specify terms to exclude from the search results using the negation keyword.
The default keyword is "not", but is configurable via settings using ``DRF_HAYSTACK_NEGATION_KEYWORD``.

.. code-block:: none

    http://example.com/api/v1/location/search/?city__not=Oslo
    http://example.com/api/v1/location/search/?city__not__contains=Los
    http://example.com/api/v1/location/search/?city__contains=Los&city__not__contains=Angeles

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


Highlighting
============

Haystack supports two kinds of `Highlighting <https://django-haystack.readthedocs.io/en/latest/highlighting.html>`_,
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
This is somewhat slower, but more configurable than the ``HaystackHighlightFilter``.

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


.. _more-like-this-label:

More Like This
==============

Some search backends supports ``More Like This`` features. In order to take advantage of this,
we have a mixin class :class:`drf_haystack.mixins.MoreLikeThisMixin`, which will append a ``more-like-this``
detail route to the base name of the ViewSet. Lets say you have a router which looks like this:

.. code-block:: python

    router = routers.DefaultRouter()
    router.register("search", viewset=SearchViewSet, base_name="search")  # MLT name will be 'search-more-like-this'.

    urlpatterns = patterns(
        "",
        url(r"^", include(router.urls))
    )

The important thing here is that the ``SearchViewSet`` class inherits from the ``MoreLikeThisMixin`` class
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


    class SearchViewSet(MoreLikeThisMixin, HaystackViewSet):
        index_models = [Person]
        serializer_class = SearchSerializer


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

.. _term-boost-label:

Term Boost
==========

.. warning::

    **BIG FAT WARNING**

    As far as I can see, the term boost functionality is implemented by the specs in the
    `Haystack documentation <https://django-haystack.readthedocs.io/en/v2.4.0/boost.html#term-boost>`_,
    however it does not really work as it should!

    When applying term boost, results are discarded from the search result, and not re-ordered by
    boost weight as they should.
    These are known problems and there exists open issues for them:

        - https://github.com/inonit/drf-haystack/issues/21
        - https://github.com/django-haystack/django-haystack/issues/1235
        - https://github.com/django-haystack/django-haystack/issues/508

    **Please do not use this unless you really know what you are doing!**

    (And please let me know if you know how to fix it!)


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

.. _faceting-label:

Faceting
========

Faceting is a way of grouping and narrowing search results by a common factor, for example we can group
all results which are registered on a certain date. Similar to :ref:`more-like-this-label`, the faceting
functionality is implemented by setting up a special ``^search/facets/$`` route on any view which inherits from the
:class:`drf_haystack.mixins.FacetMixin` class.


.. note::

    Options used for faceting is **not** portable across search backends. Make sure to provide
    options suitable for the backend you're using.


First, read the `Haystack faceting docs <https://django-haystack.readthedocs.io/en/latest/faceting.html>`_ and set up
your search index for faceting.

Serializing faceted counts
--------------------------

Faceting is a little special in terms that it *does not* care about SearchQuerySet filtering. Faceting is performed
by calling the ``SearchQuerySet().facet(field, **options)`` and ``SearchQuerySet().date_facet(field, **options)``
methods, which will apply facets to the SearchQuerySet. Next we need to call the ``SearchQuerySet().facet_counts()``
in order to retrieve a dictionary with all the *counts* for the faceted fields.
We have a special ``HaystackFacetSerializer`` class which is designed to serialize these results.

.. tip::

    It *is* possible to perform faceting on a subset of the queryset, in which case you'd have to override the
    ``get_queryset()`` method of the view to limit the queryset before it is passed on to the
    ``filter_facet_queryset()`` method.

Any serializer subclassed from the ``HaystackFacetSerializer`` is expected to have a ``field_options`` dictionary
containing a set of default options passed to ``facet()`` and ``date_facet()``.

**Facet serializer example**

.. code-block:: python

    class PersonFacetSerializer(HaystackFacetSerializer):

        serialize_objects = False  # Setting this to True will serialize the
                                   # queryset into an `objects` list. This
                                   # is useful if you need to display the faceted
                                   # results. Defaults to False.
        class Meta:
            index_classes = [PersonIndex]
            fields = ["firstname", "lastname", "created"]
            field_options = {
                "firstname": {},
                "lastname": {},
                "created": {
                    "start_date": datetime.now() - timedelta(days=3 * 365),
                    "end_date": datetime.now(),
                    "gap_by": "month",
                    "gap_amount": 3
                }
            }

The declared ``field_options`` will be used as default options when faceting is applied to the queryset, but can be
overridden by supplying query string parameters in the following format.

    .. code-block:: none

        ?firstname=limit:1&created=start_date:20th May 2014,gap_by:year

Each field can be fed options as ``key:value`` pairs. Multiple ``key:value`` pairs can be supplied and
will be separated by the ``view.lookup_sep`` attribute (which defaults to comma). Any ``start_date`` and ``end_date``
parameters will be parsed by the python-dateutil
`parser() <https://labix.org/python-dateutil#head-a23e8ae0a661d77b89dfb3476f85b26f0b30349c>`_ (which can handle most
common date formats).

    .. note::

        - The ``HaystackFacetFilter`` parses query string parameter options, separated with the ``view.lookup_sep``
          attribute. Each option is parsed as ``key:value`` pairs where the ``:`` is a hardcoded separator. Setting
          the ``view.lookup_sep`` attribute to ``":"`` will raise an AttributeError.

        - The date parsing in the ``HaystackFacetFilter`` does intentionally blow up if fed a string format it can't
          handle. No exception handling is done, so make sure to convert values to a format you know it can handle
          before passing it to the filter. Ie., don't let your users feed their own values in here ;)

    .. warning::

        Do *not* use the ``HaystackFacetFilter`` in the regular ``filter_backends`` list on the serializer.
        It will almost certainly produce errors or weird results. Faceting filters should go in the
        ``facet_filter_backends`` list.

**Example serialized content**

The serialized content will look a little different than the default Haystack faceted output.
The top level items will *always* be **queries**, **fields** and **dates**, each containing a subset of fields
matching the category. In the example below, we have faceted on the fields *firstname* and *lastname*, which will
make them appear under the **fields** category. We also have faceted on the date field *created*, which will show up
under the **dates** category. Next, each faceted result will have a ``text``, ``count`` and ``narrow_url``
attribute which should be quite self explaining.

    .. code-block:: json

        {
          "queries": {},
          "fields": {
            "firstname": [
              {
                "text": "John",
                "count": 3,
                "narrow_url": "http://example.com/api/v1/search/facets/?selected_facets=firstname_exact%3AJohn"
              },
              {
                "text": "Randall",
                "count": 2,
                "narrow_url": "http://example.com/api/v1/search/facets/?selected_facets=firstname_exact%3ARandall"
              },
              {
                "text": "Nehru",
                "count": 2,
                "narrow_url": "http://example.com/api/v1/search/facets/?selected_facets=firstname_exact%3ANehru"
              }
            ],
            "lastname": [
              {
                "text": "Porter",
                "count": 2,
                "narrow_url": "http://example.com/api/v1/search/facets/?selected_facets=lastname_exact%3APorter"
              },
              {
                "text": "Odonnell",
                "count": 2,
                "narrow_url": "http://example.com/api/v1/search/facets/?selected_facets=lastname_exact%3AOdonnell"
              },
              {
                "text": "Hood",
                "count": 2,
                "narrow_url": "http://example.com/api/v1/search/facets/?selected_facets=lastname_exact%3AHood"
              }
            ]
          },
          "dates": {
            "created": [
              {
                "text": "2015-05-15T00:00:00",
                "count": 100,
                "narrow_url": "http://example.com/api/v1/search/facets/?selected_facets=created_exact%3A2015-05-15+00%3A00%3A00"
              }
            ]
          }
        }


Serializing faceted results
---------------------------

When a ``HaystackFacetSerializer`` class determines what fields to serialize, it will check
the ``serialize_objects`` class attribute to see if it is ``True`` or ``False``. Setting this value to ``True``
will add an additional ``objects`` field to the serialized results, which will contain the results for the
faceted ``SearchQuerySet``. The results will be serialized using the view's ``serializer_class``.

**Example faceted results with paginated serialized objects**

.. code-block:: json

    {
      "fields": {
        "firstname": [
          {"...": "..."}
        ],
        "lastname": [
          {"...": "..."}
        ]
      },
      "dates": {
        "created": [
          {"...": "..."}
        ]
      },
      "queries": {},
      "objects": {
        "count": 3,
        "next": "http://example.com/api/v1/search/facets/?page=2&selected_facets=firstname_exact%3AJohn",
        "previous": null,
        "results": [
          {
            "lastname": "Baker",
            "firstname": "John",
            "full_name": "John Baker",
            "text": "John Baker\n"
          },
          {
            "lastname": "McClane",
            "firstname": "John",
            "full_name": "John McClane",
            "text": "John McClane\n"
          }
        ]
      }
    }



Setting up the view
-------------------

Any view that inherits the :class:`drf_haystack.mixins.FacetMixin` will have a special
`action route <http://www.django-rest-framework.org/api-guide/viewsets/#marking-extra-actions-for-routing>`_ added as
``^<view-url>/facets/$``. This view action will not care about regular filtering but will by default use the
``HaystackFacetFilter`` to perform filtering.

.. note::

    In order to avoid confusing the filtering mechanisms in Django Rest Framework, the ``FacetMixin``
    class has a couple of hooks for dealing with faceting, namely:

        - ``facet_filter_backends`` - A list of filter backends that will be used to apply faceting to the queryset.
          Defaults to ``HaystackFacetFilter``, which should be sufficient in most cases.
        - ``facet_serializer_class`` - The ``HaystackFacetSerializer`` subclass instance that will be used for
          serializing the result.
        - ``filter_facet_queryset()`` - Works exactly as the normal ``filter_queryset()`` method, but will only filter
          on backends in the ``facet_filter_backends`` list.
        - ``get_facet_serializer_class()`` - Returns the ``facet_serializer_class`` class attribute.
        - ``get_facet_serializer()`` - Instantiates and returns the ``HaystackFacetSerializer`` class returned from
          ``get_facet_serializer_class()``.


In order to set up a view which can respond to regular queries under ie ``^search/$`` and faceted queries under
``^search/facets/$``, we could do something like this.

.. code-block:: python

    class SearchPersonViewSet(FacetMixin, HaystackViewSet):

        index_models = [MockPerson]

        # This will be used to filter and serialize regular queries as well
        # as the results if the `facet_serializer_class` has the
        # `serialize_objects = True` set.
        serializer_class = SearchSerializer
        filter_backends = [HaystackHighlightFilter, HaystackAutocompleteFilter]

        # This will be used to filter and serialize faceted results
        facet_serializer_class = PersonFacetSerializer  # See example above!
        facet_filter_backends = [HaystackFacetFilter]   # This is the default facet filter, and
                                                        # can be left out.


Narrowing
---------

As we have seen in the examples above, the ``HaystackFacetSerializer`` will add a ``narrow_url`` attribute to each
result it serializes. Follow that link to narrow the search result.

The ``narrow_url`` is constructed like this:

    - Read all query parameters from the request
    - Get a list of ``selected_facets``
    - Update the query parameters by adding the current item to ``selected_facets``
    - Return a ``serializers.Hyperlink`` with URL encoded query parameters

This means that for each drill-down performed, the original query parameters will be kept in order to make
the ``HaystackFacetFilter`` happy. Additionally, all the previous ``selected_facets`` will be kept and applied
to narrow the ``SearchQuerySet`` properly.

**Example narrowed result**

    .. code-block:: json

        {
          "queries": {},
          "fields": {
            "firstname": [
              {
                "text": "John",
                "count": 1,
                "narrow_url": "http://example.com/api/v1/search/facets/?selected_facets=firstname_exact%3AJohn&selected_facets=lastname_exact%3AMcLaughlin"
              }
            ],
            "lastname": [
              {
                "text": "McLaughlin",
                "count": 1,
                "narrow_url": "http://example.com/api/v1/search/facets/?selected_facets=firstname_exact%3AJohn&selected_facets=lastname_exact%3AMcLaughlin"
              }
            ]
          },
          "dates": {
            "created": [
              {
                "text": "2015-05-15T00:00:00",
                "count": 1,
                "narrow_url": "http://example.com/api/v1/search/facets/?selected_facets=firstname_exact%3AJohn&selected_facets=lastname_exact%3AMcLaughlin&selected_facets=created_exact%3A2015-05-15+00%3A00%3A00"
              }
            ]
          }
        }

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


Reusing Model serializers
=========================

It may be useful to be able to use existing model serializers to return data from search requests in the same format
as used elsewhere in your API.  This can be done by modifying the ``to_representation`` method of your serializer to
use the ``instance.object`` instead of the search result instance.  As a convenience, a mixin class is provided that
does just that.

.. class:: drf_haystack.serializers.HaystackSerializerMixin

An example using the mixin might look like the following:

.. code-block:: python

    class PersonSerializer(serializers.ModelSerializer):
        class Meta:
            model = Person
            fields = ("id", "firstname", "lastname")

    class PersonSearchSerializer(HaystackSerializerMixin, PersonSerializer):
        class Meta(PersonSerializer.Meta):
            search_fields = ("text", )

The results from a search would then contain the fields from the ``PersonSerializer`` rather than fields from the
search index.

.. note::

    If your model serializer specifies a ``fields`` attribute in its Meta class, then the search serializer must
    specify a ``search_fields`` attribute in its Meta class if you intend to search on any search index fields
    that are not in the model serializer fields (e.g. 'text')

.. warning::

    It should be noted that doing this will retrieve the underlying object which means a database hit.  Thus, it will
    not be as performant as only retrieving data from the search index.  If performance is a concern, it would be
    better to recreate the desired data structure and store it in the search index.


.. _multiple-search-indexes-label:

Multiple Search indexes
=======================

So far, we have only used one class in the ``index_classes`` attribute of our serializers.  However, you are able to specify
a list of them.  This can be useful when your search engine has indexed multiple models and you want to provide aggregate
results across two or more of them.  To use the default multiple index support, simply add multiple indexes the ``index_classes``
list

.. code-block:: python

    class PersonIndex(indexes.SearchIndex, indexes.Indexable):
        text = indexes.CharField(document=True, use_template=True)
        firstname = indexes.CharField(model_attr="first_name")
        lastname = indexes.CharField(model_attr="last_name")

        def get_model(self):
            return Person

    class PlaceIndex(indexes.SearchIndex, indexes.Indexable):
        text = indexes.CharField(document=True, use_template=True)
        address = indexes.CharField(model_attr="address")

        def get_model(self):
            return Place

    class ThingIndex(indexes.SearchIndex, indexes.Indexable):
        text = indexes.CharField(document=True, use_template=True)
        name = indexes.CharField(model_attr="name")

        def get_model(self):
            return Thing

    class AggregateSerializer(HaystackSerializer):

        class Meta:
            index_classes = [PersonIndex, PlaceIndex, ThingIndex]
            fields = ["firstname", "lastname", "address", "name"]


    class AggregateSearchViewSet(HaystackViewSet):

        serializer_class = AggregateSerializer

.. note::

    The ``AggregateSearchViewSet`` class above omits the optional ``index_models`` attribute.  This way results from all the
    models are returned.

The result from searches using multiple indexes is a list of objects, each of which contains only the fields appropriate to
the model from which the result came.  For instance if a search returned a list containing one each of the above models, it
might look like the following:

.. code-block:: javascript

    [
        {
            "text": "John Doe",
            "firstname": "John",
            "lastname": "Doe"
        },
        {
            "text": "123 Doe Street",
            "address": "123 Doe Street"
        },
        {
            "text": "Doe",
            "name": "Doe"
        }
    ]

Declared fields
---------------

You can include field declarations in the serializer class like normal.  Depending on how they are named, they will be
treated as common fields and added to every result or as specific to results from a particular index.

Common fields are declared as you would any serializer field.  Index-specific fields must be prefixed with "_<index class name>__".
The following example illustrates this usage:

.. code-block:: python

    class AggregateSerializer(HaystackSerializer):
        extra = serializers.CharField()
        _ThingIndex__number = serializers.IntegerField()

        class Meta:
            index_classes = [PersonIndex, PlaceIndex, ThingIndex]
            fields = ["firstname", "lastname", "address", "name"]

        def get_extra(self):
            return "whatever"

        def get__ThingIndex__number(self):
            return 42

The results of a search might then look like the following:

.. code-block:: javascript

    [
        {
            "text": "John Doe",
            "firstname": "John",
            "lastname": "Doe",
            "extra": "whatever"
        },
        {
            "text": "123 Doe Street",
            "address": "123 Doe Street",
            "extra": "whatever"
        },
        {
            "text": "Doe",
            "name": "Doe",
            "extra": "whatever",
            "number": 42
        }
    ]

Multiple Serializers
--------------------

Alternatively, you can specify a 'serializers' attribute on your Meta class to use a different serializer class
for different indexes as show below:

.. code-block:: python

    class AggregateSearchSerializer(HaystackSerializer):
        class Meta:
            serializers = {
                PersonIndex: PersonSearchSerializer,
                PlaceIndex: PlaceSearchSerializer,
                ThingIndex: ThingSearchSerializer
            }

The ``serializers`` attribute is the important thing here, It's a dictionary with ``SearchIndex`` classes as
keys and ``Serializer`` classes as values.  Each result in the list of results from a search that contained
items from multiple indexes would be serialized according to the appropriate serializer.
