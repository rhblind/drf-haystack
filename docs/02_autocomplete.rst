.. _autocomplete-label:

Autocomplete
============

Some kind of data such as ie. cities and zip codes could be useful to autocomplete.
We have a Django REST Framework filter for performing autocomplete queries. It works
quite like the regular :class:`drf_haystack.filters.HaystackFilter` but *must* be run
against an ``NgramField`` or ``EdgeNgramField`` in order to work properly. The main
difference is that while the HaystackFilter performs a bitwise ``OR`` on terms for the
same parameters, the :class:`drf_haystack.filters.HaystackAutocompleteFilter` reduce query
parameters down to a single filter (using an ``SQ`` object), and performs a bitwise ``AND``.

By adding a list or tuple of ``ignore_fields`` to the serializer's Meta class,
we can tell the REST framework to ignore these fields. This is handy in cases,
where you do not want to serialize and transfer the content of a text, or n-gram
index down to the client.

An example using the autocomplete filter might look something like this.


.. code-block:: python

    from drf_haystack.filters import HaystackAutocompleteFilter
    from drf_haystack.serializers import HaystackSerializer
    from drf_haystack.viewsets import HaystackViewSet

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

