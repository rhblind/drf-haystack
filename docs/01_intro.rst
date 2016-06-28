.. _basic-usage-label:

===========
Basic Usage
===========

Usage is best demonstrated with some simple examples.

.. warning::

    The code here is for demonstration purposes only! It might work (or not, I haven't
    tested), but as always, don't blindly copy code from the internet.

Examples
========

models.py
---------

Let's say we have an app which contains a model `Location`. It could look something like this.

.. code-block:: python

    #
    # models.py
    #

    from django.db import models
    from haystack.utils.geo import Point


    class Location(models.Model):

        latitude = models.FloatField()
        longitude = models.FloatField()
        address = models.CharField(max_length=100)
        city = models.CharField(max_length=30)
        zip_code = models.CharField(max_length=10)

        created = models.DateTimeField(auto_now_add=True)
        updated = models.DateTimeField(auto_now=True)

        def __str__(self):
            return self.address

        @property
        def coordinates(self):
            return Point(self.longitude, self.latitude)


.. _search-index-example-label:

search_indexes.py
-----------------

We would have to make a ``search_indexes.py`` file for haystack to pick it up.

.. code-block:: python

    #
    # search_indexes.py
    #

    from django.utils import timezone
    from haystack import indexes
    from .models import Location


    class LocationIndex(indexes.SearchIndex, indexes.Indexable):

        text = indexes.CharField(document=True, use_template=True)
        address = indexes.CharField(model_attr="address")
        city = indexes.CharField(model_attr="city")
        zip_code = indexes.CharField(model_attr="zip_code")

        autocomplete = indexes.EdgeNgramField()
        coordinates = indexes.LocationField(model_attr="coordinates")

        @staticmethod
        def prepare_autocomplete(obj):
            return " ".join((
                obj.address, obj.city, obj.zip_code
            ))

        def get_model(self):
            return Location

        def index_queryset(self, using=None):
            return self.get_model().objects.filter(
                created__lte=timezone.now()
            )


views.py
--------

For a generic Django REST Framework view, you could do something like this.

.. code-block:: python

    #
    # views.py
    #

    from drf_haystack.serializers import HaystackSerializer
    from drf_haystack.viewsets import HaystackViewSet

    from .models import Location
    from .search_indexes import LocationIndex


    class LocationSerializer(HaystackSerializer):

        class Meta:
            # The `index_classes` attribute is a list of which search indexes
            # we want to include in the search.
            index_classes = [LocationIndex]

            # The `fields` contains all the fields we want to include.
            # NOTE: Make sure you don't confuse these with model attributes. These
            # fields belong to the search index!
            fields = [
                "text", "address", "city", "zip_code", "autocomplete"
            ]


    class LocationSearchView(HaystackViewSet):

        # `index_models` is an optional list of which models you would like to include
        # in the search result. You might have several models indexed, and this provides
        # a way to filter out those of no interest for this particular view.
        # (Translates to `SearchQuerySet().models(*index_models)` behind the scenes.
        index_models = [Location]

        serializer_class = LocationSerializer


urls.py
-------

Finally, hook up the views in your `urls.py` file.

.. note::

    Make sure you specify the `base_name` attribute when wiring up the view in the router.
    Since we don't have any single `model` for the view, it is impossible for the router to
    automatically figure out the base name for the view.

.. code-block:: python

    #
    # urls.py
    #

    from django.conf.urls import patterns, url, include
    from rest_framework import routers

    from .views import LocationSearchView

    router = routers.DefaultRouter()
    router.register("location/search", LocationSearchView, base_name="location-search")


    urlpatterns = patterns(
        "",
        url(r"/api/v1/", include(router.urls)),
    )


Query time!
-----------

Now that we have a view wired up, we can start using it.
By default, the `HaystackViewSet` (which, more importantly inherits the `HaystackGenericAPIView`
class) is set up to use the `HaystackFilter`. This is the most basic filter included and can do
basic search by querying any of the field included in the `fields` attribute on the
`Serializer`.

.. code-block:: none

    http://example.com/api/v1/location/search/?city=Oslo

Would perform a query looking up all documents where the `city field` equals "Oslo".


Field Lookups
.............

You can also use field lookups in your field queries. See the
Haystack `field lookups <https://django-haystack.readthedocs.io/en/latest/searchqueryset_api.html?highlight=lookups#id1>`_
documentation for info on what lookups are available.  A query using a lookup might look like the
following:

.. code-block:: none

    http://example.com/api/v1/location/search/?city__startswith=Os

This would perform a query looking up all documents where the `city field` started with "Os".
You might get "Oslo", "Osaka", and "Ostrava".

Term Negation
.............

You can also specify terms to exclude from the search results using the negation keyword.
The default keyword is ``not``, but is configurable via settings using ``DRF_HAYSTACK_NEGATION_KEYWORD``.

.. code-block:: none

    http://example.com/api/v1/location/search/?city__not=Oslo
    http://example.com/api/v1/location/search/?city__not__contains=Los
    http://example.com/api/v1/location/search/?city__contains=Los&city__not__contains=Angeles

