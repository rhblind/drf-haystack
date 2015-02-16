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
`EdgeNgramField` in order to work properly. The main difference is that wile the
HaystackFilter performs a bitwise `OR` on terms for the same parameters, the
`HaystackAutocompleteFilter` reduce query parameters down to a single filter
(using an `SQ` object), and performs a bitwise `AND`.

.. autoclass:: drf_haystack.filters.HaystackAutocompleteFilter


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

        class Meta:
            index_models = [Location]
            serializer_class = AutocompleteSerializer
            filter_backends = [HaystackAutocompleteFilter]


GEO Locations
=============

Some search backends support geo spatial searching. In order to take advantage of this we
have the `HaystackGEOSpatialFilter`.

.. autoclass:: drf_haystack.filters.HaystackGEOSpatialFilter

.. todo:: Write this section!