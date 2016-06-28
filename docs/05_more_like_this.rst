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

The important thing here is that the ``SearchViewSet`` class inherits from the
:class:`drf_haystack.mixins.MoreLikeThisMixin` class in order to get the ``more-like-this`` route automatically added.
The view name will be ``{base_name}-more-like-this``, which in this case would be for example ``search-more-like-this``.


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
