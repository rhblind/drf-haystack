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
implemented as a :class:`drf_haystack.filters.HaystackBoostFilter` filter backend.
The ``HaystackBoostFilter`` does not perform any filtering by itself, and should therefore be combined with
some other filter that does, for example the :class:`drf_haystack.filters.HaystackFilter`.

.. code-block:: python

    from drf_haystack.filters import HaystackBoostFilter

    class SearchViewSet(HaystackViewSet):
        ...
        filter_backends = [HaystackFilter, HaystackBoostFilter]


The filter expects the query string to contain a ``boost`` parameter, which is a comma separated string
of the term to boost and the boost value. The boost value must be either an integer or float value.

**Example query**

.. code-block:: none

    /api/v1/search/?firstname=robin&boost=hood,1.1

The query above will first filter on ``firstname=robin`` and next apply a slight boost on any document containing
the word ``hood``.

.. note::

    Term boost are only applied on terms existing in the ``document field``.
