.. _highlighting-label:

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
:class:`drf_haystack.filters.HaystackHighlightFilter` to the ``filter_backends`` in your view. The ``HaystackSerializer`` will
check if your queryset has highlighting enabled, and render an additional ``highlighted`` field to
your result. The highlighted words will be encapsulated in an ``<em>words go here</em>`` html tag.


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
It is implemented as :class:`drf_haystack.serializers.HighlighterMixin` mixin class, and must be applied on the ``Serializer``.
This is somewhat slower, but more configurable than the :class:`drf_haystack.filters.HaystackHighlightFilter` filter class.

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
