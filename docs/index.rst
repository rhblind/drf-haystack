==================================
Haystack for Django REST Framework
==================================

Contents:

.. toctree::
   :maxdepth: 2

   basic_usage
   advanced_usage

=====
About
=====
Small library aiming to simplify using Haystack with Django REST Framework

Features
========

Supported Python versions:

    - Python 2.6
        - Django 1.5 and 1.6
    - Python 2.7, 3.3 and 3.4
        - Django 1.5, 1.6, 1.7 and 1.8


Installation
============
It's in the cheese shop!

.. code-block:: none

    $ pip install drf-haystack


Requirements
============
    - Django
    - Django REST Framework
    - Haystack (and a supported search engine such as Solr, Elasticsearch, Whoosh, etc.)
    - geopy


Changelog
=========

v1.0
----
*Release date: 2015-02-14*

    - Initial release.


v1.1
----
*Release date: 2015-02-16*

    - Full coverage (almost) test suite
    - Documentation
    - Beta release Development classifier

v1.2
----
*Release date: 2015-03-23*

    - Fixed `MissingDependency` error when using another search backend than Elasticsearch.
    - Fixed converting distance to D object before filtering in HaystackGEOSpatialFilter.
    - Added Python 3 classifier.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

