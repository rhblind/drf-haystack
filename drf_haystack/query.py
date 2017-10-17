# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import operator
import warnings
from itertools import chain

from django.utils import six
from django.utils.six.moves import zip
from dateutil import parser

from drf_haystack import constants
from drf_haystack.utils import merge_dict


class BaseQueryBuilder(object):
    """
    Query builder base class.
    """

    def __init__(self, backend, view):
        self.backend = backend
        self.view = view

    def build_query(self, **filters):
        """
        :param dict[str, list[str]] filters: is an expanded QueryDict or
          a mapping of keys to a list of parameters.
        """
        raise NotImplementedError("You should override this method in subclasses.")

    @staticmethod
    def tokenize(stream, separator):
        """
        Tokenize and yield query parameter values.

        :param stream: Input value
        :param separator: Character to use to separate the tokens.
        :return:
        """
        for value in stream:
            for token in value.split(separator):
                if token:
                    yield token.strip()


class BoostQueryBuilder(BaseQueryBuilder):
    """
    Query builder class for adding boost to queries.
    """

    def build_query(self, **filters):

        applicable_filters = None
        query_param = getattr(self.backend, "query_param", None)

        value = filters.pop(query_param, None)
        if value:
            try:
                term, val = chain.from_iterable(zip(self.tokenize(value, self.view.lookup_sep)))
            except ValueError:
                raise ValueError("Cannot convert the '%s' query parameter to a valid boost filter."
                                 % query_param)
            else:
                try:
                    applicable_filters = {"term": term, "boost": float(val)}
                except ValueError:
                    raise ValueError("Cannot convert boost to float value. Make sure to provide a "
                                     "numerical boost value.")

        return applicable_filters


class FilterQueryBuilder(BaseQueryBuilder):
    """
    Query builder class suitable for doing basic filtering.
    """

    def __init__(self, backend, view):
        super(FilterQueryBuilder, self).__init__(backend, view)

        assert getattr(self.backend, "default_operator", None) in (operator.and_, operator.or_), (
            "%(cls)s.default_operator must be either 'operator.and_' or 'operator.or_'." % {
                "cls": self.backend.__class__.__name__
            })
        self.default_operator = self.backend.default_operator

    def build_query(self, **filters):
        """
        Creates a single SQ filter from querystring parameters that correspond to the SearchIndex fields
        that have been "registered" in `view.fields`.

        Default behavior is to `OR` terms for the same parameters, and `AND` between parameters. Any
        querystring parameters that are not registered in `view.fields` will be ignored.

        :param dict[str, list[str]] filters: is an expanded QueryDict or a mapping of keys to a list of
        parameters.
        """

        applicable_filters = []
        applicable_exclusions = []

        for param, value in filters.items():
            # Skip if the parameter is not listed in the serializer's `fields`
            # or if it's in the `exclude` list.
            excluding_term = False
            param_parts = param.split("__")
            base_param = param_parts[0]  # only test against field without lookup
            negation_keyword = constants.DRF_HAYSTACK_NEGATION_KEYWORD
            if len(param_parts) > 1 and param_parts[1] == negation_keyword:
                excluding_term = True
                param = param.replace("__%s" % negation_keyword, "")  # haystack wouldn't understand our negation

            if self.view.serializer_class:
                if hasattr(self.view.serializer_class.Meta, 'field_aliases'):
                    old_base = base_param
                    base_param = self.view.serializer_class.Meta.field_aliases.get(base_param, base_param)
                    param = param.replace(old_base, base_param)  # need to replace the alias

                fields = getattr(self.view.serializer_class.Meta, 'fields', [])
                exclude = getattr(self.view.serializer_class.Meta, 'exclude', [])
                search_fields = getattr(self.view.serializer_class.Meta, 'search_fields', [])

                if ((fields or search_fields) and base_param not in chain(fields, search_fields)) or base_param in exclude or not value:
                    continue

            field_queries = []
            for token in self.tokenize(value, self.view.lookup_sep):
                field_queries.append(self.view.query_object((param, token)))

            field_queries = [fq for fq in field_queries if fq]
            if len(field_queries) > 0:
                term = six.moves.reduce(operator.or_, field_queries)
                if excluding_term:
                    applicable_exclusions.append(term)
                else:
                    applicable_filters.append(term)

        applicable_filters = six.moves.reduce(
            self.default_operator, filter(lambda x: x, applicable_filters)) if applicable_filters else []

        applicable_exclusions = six.moves.reduce(
            self.default_operator, filter(lambda x: x, applicable_exclusions)) if applicable_exclusions else []

        return applicable_filters, applicable_exclusions


class FacetQueryBuilder(BaseQueryBuilder):
    """
    Query builder class suitable for constructing faceted queries.
    """

    def build_query(self, **filters):
        """
        Creates a dict of dictionaries suitable for passing to the  SearchQuerySet `facet`,
        `date_facet` or `query_facet` method. All key word arguments should be wrapped in a list.

        :param view: API View
        :param dict[str, list[str]] filters: is an expanded QueryDict or a mapping
        of keys to a list of parameters.
        """
        field_facets = {}
        date_facets = {}
        query_facets = {}
        facet_serializer_cls = self.view.get_facet_serializer_class()

        if self.view.lookup_sep == ":":
            raise AttributeError("The %(cls)s.lookup_sep attribute conflicts with the HaystackFacetFilter "
                                 "query parameter parser. Please choose another `lookup_sep` attribute "
                                 "for %(cls)s." % {"cls": self.view.__class__.__name__})

        fields = facet_serializer_cls.Meta.fields
        exclude = facet_serializer_cls.Meta.exclude
        field_options = facet_serializer_cls.Meta.field_options

        for field, options in filters.items():

            if field not in fields or field in exclude:
                continue

            field_options = merge_dict(field_options, {field: self.parse_field_options(self.view.lookup_sep, *options)})

        valid_gap = ("year", "month", "day", "hour", "minute", "second")
        for field, options in field_options.items():
            if any([k in options for k in ("start_date", "end_date", "gap_by", "gap_amount")]):

                if not all(("start_date", "end_date", "gap_by" in options)):
                    raise ValueError("Date faceting requires at least 'start_date', 'end_date' "
                                     "and 'gap_by' to be set.")

                if not options["gap_by"] in valid_gap:
                    raise ValueError("The 'gap_by' parameter must be one of %s." % ", ".join(valid_gap))

                options.setdefault("gap_amount", 1)
                date_facets[field] = field_options[field]

            else:
                field_facets[field] = field_options[field]

        return {
            "date_facets": date_facets,
            "field_facets": field_facets,
            "query_facets": query_facets
        }

    def parse_field_options(self, *options):
        """
        Parse the field options query string and return it as a dictionary.
        """
        defaults = {}
        for option in options:
            if isinstance(option, six.text_type):
                tokens = [token.strip() for token in option.split(self.view.lookup_sep)]

                for token in tokens:
                    if not len(token.split(":")) == 2:
                        warnings.warn("The %s token is not properly formatted. Tokens need to be "
                                      "formatted as 'token:value' pairs." % token)
                        continue

                    param, value = token.split(":", 1)

                    if any([k == param for k in ("start_date", "end_date", "gap_amount")]):

                        if param in ("start_date", "end_date"):
                            value = parser.parse(value)

                        if param == "gap_amount":
                            value = int(value)

                    defaults[param] = value

        return defaults


class SpatialQueryBuilder(BaseQueryBuilder):
    """
    Query builder class suitable for construction spatial queries.
    """

    def __init__(self, backend, view):
        super(SpatialQueryBuilder, self).__init__(backend, view)

        assert getattr(self.backend, "point_field", None) is not None, (
            "%(cls)s.point_field cannot be None. Set the %(cls)s.point_field "
            "to the name of the `LocationField` you want to filter on your index class." % {
                "cls": self.backend.__class__.__name__
            })

        try:
            from haystack.utils.geo import D, Point
            self.D = D
            self.Point = Point
        except ImportError:
            warnings.warn("Make sure you've installed the `libgeos` library. "
                          "Run `apt-get install libgeos` on debian based linux systems, "
                          "or `brew install geos` on OS X.")
            raise

    def build_query(self, **filters):
        """
        Build queries for geo spatial filtering.

        Expected query parameters are:
         - a `unit=value` parameter where the unit is a valid UNIT in the
           `django.contrib.gis.measure.Distance` class.
         - `from` which must be a comma separated latitude and longitude.

         Example query:
             /api/v1/search/?km=10&from=59.744076,10.152045

             Will perform a `dwithin` query within 10 km from the point
             with latitude 59.744076 and longitude 10.152045.
        """

        applicable_filters = None

        filters = dict((k, filters[k]) for k in chain(self.D.UNITS.keys(), [constants.DRF_HAYSTACK_SPATIAL_QUERY_PARAM]) if k in filters)
        distance = dict((k, v) for k, v in filters.items() if k in self.D.UNITS.keys())

        try:
            latitude, longitude = map(float, self.tokenize(filters[constants.DRF_HAYSTACK_SPATIAL_QUERY_PARAM], self.view.lookup_sep))
            point = self.Point(longitude, latitude, srid=constants.GEO_SRID)
        except ValueError:
            raise ValueError("Cannot convert `from=latitude,longitude` query parameter to "
                             "float values. Make sure to provide numerical values only!")
        except KeyError:
            # If the user has not provided any `from` query string parameter,
            # just return.
            pass
        else:
            for unit in distance.keys():
                if not len(distance[unit]) == 1:
                    raise ValueError("Each unit must have exactly one value.")
                distance[unit] = float(distance[unit][0])

            if point and distance:
                applicable_filters = {
                    "dwithin": {
                        "field": self.backend.point_field,
                        "point": point,
                        "distance": self.D(**distance)
                    },
                    "distance": {
                        "field": self.backend.point_field,
                        "point": point
                    }
                }

        return applicable_filters
