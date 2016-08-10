.. _tips-n-tricks-label:

Tips'n Tricks
=============

Reusing Model serializers
-------------------------

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


Regular Search View
-------------------

Sometimes you might not need all the bells and whistles of a ``ViewSet``,
but can do with a regular view. In such scenario you could do something like this.

.. code-block:: python

    #
    # views.py
    #

    from rest_framework.mixins import ListModelMixin
    from drf_haystack.generics import HaystackGenericAPIView


    class SearchView(ListModelMixin, HaystackGenericAPIView):

        serializer_class = LocationSerializer

        def get(self, request, *args, **kwargs):
            return self.list(request, *args, **kwargs)


    #
    # urls.py
    #

    urlpatterns = (
       ...
        url(r'^search/', SearchView.as_view()),
       ...
    )

You can also use `FacetMixin` or `MoreLikeThisMixin` in your regular views as well.

.. code-block:: python

    #
    # views.py
    #

    from rest_framework.mixins import ListModelMixin
    from drf_haystack.mixins import FacetMixin
    from drf_haystack.generics import HaystackGenericAPIView


    class SearchView(ListModelMixin, FacetMixin, HaystackGenericAPIView):
        index_models = [Project]
        serializer_class = ProjectListSerializer
        facet_serializer_class = ProjectListFacetSerializer

        pagination_class = BasicPagination
        permission_classes = (AllowAny,)

        def get(self, request, *args, **kwargs):
            return self.facets(request, *args, **kwargs)
