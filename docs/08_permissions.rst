.. _permissions-label:

Permissions
===========

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
