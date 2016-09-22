.. _multiple-indexes-label:

Multiple search indexes
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

.. warning::

    If a field name is shared across serializers, and one serializer overrides the field mapping, the overridden
    mapping will be used for *all* serializers. See the example below for more details.

.. code-block:: python

    from rest_framework import serializers

    class PersonSearchSerializer(HaystackSerializer):
        # NOTE: This override will be used for both Person and Place objects.
        name = serializers.SerializerMethodField()

        class Meta:
            fields = ['name']

    class PlaceSearchSerializer(HaystackSerializer):
        class Meta:
            fields = ['name']

    class AggregateSearchSerializer(HaystackSerializer):
        class Meta:
            serializers = {
                PersonIndex: PersonSearchSerializer,
                PlaceIndex: PlaceSearchSerializer,
                ThingIndex: ThingSearchSerializer
            }
