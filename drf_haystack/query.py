import operator
import warnings
from itertools import chain

import six
from dateutil import parser
from django.core.exceptions import ImproperlyConfigured
from drf_haystack.utils import merge_dict
from . import constants


class QueryBuilder:

    """
    Builds query parameters for haystack filters.
    """

    def build_query(self, view, **kwargs):
        """
        Creates a single SQ filter from querystring parameters that correspond to the SearchIndex fields
        that have been "registered" in `view.fields`.

        Default behavior is to `OR` terms for the same parameters, and `AND` between parameters. Any
        querystring parameters that are not registered in `view.fields` will be ignored.

        :param view:
        :param dict[str, list[str]] kwargs: is an expanded QueryDict or a mapping of keys to a list of
        parameters.
        """

        terms = []
        exclude_terms = []

        for param, value in kwargs.items():
            # Skip if the parameter is not listed in the serializer's `fields`
            # or if it's in the `exclude` list.
            excluding_term = False
            param_parts = param.split("__")
            base_param = param_parts[0]  # only test against field without lookup
            negation_keyword = constants.DRF_HAYSTACK_NEGATION_KEYWORD
            if len(param_parts) > 1 and param_parts[1] == negation_keyword:
                excluding_term = True
                param = param.replace("__%s" % negation_keyword, "")  # haystack wouldn't understand our negation

            if view.serializer_class:
                if view.serializer_class.Meta.field_aliases:
                    old_base = base_param
                    base_param = view.serializer_class.Meta.field_aliases.get(base_param, base_param)
                    param = param.replace(old_base, base_param)  # need to replace the alias

                fields = view.serializer_class.Meta.fields
                exclude = view.serializer_class.Meta.exclude
                search_fields = view.serializer_class.Meta.search_fields

                if ((fields or search_fields) and base_param not in chain(fields, search_fields)) or base_param in exclude or not value:
                    continue

            field_queries = []
            for token in self.tokenize(value, view.lookup_sep):
                field_queries.append(view.query_object((param, token)))

            term = six.moves.reduce(operator.or_, filter(lambda x: x, field_queries))
            if excluding_term:
                exclude_terms.append(term)
            else:
                terms.append(term)

        terms = six.moves.reduce(operator.and_, filter(lambda x: x, terms)) if terms else []
        exclude_terms = six.moves.reduce(operator.and_, filter(lambda x: x, exclude_terms)) if exclude_terms else []
        return terms, exclude_terms

    def build_facet_query(self, view, **kwargs):
        """
        Creates a dict of dictionaries suitable for passing to the SearchQuerySet ``facet``, ``date_facet``
        or ``query_facet`` method. All key word arguments should be wrapped in a list.

        :param view:
        :param dict[str, list[str]] kwargs: is an expanded QueryDict or a mapping of keys to a list of
        parameters.
        """
        field_facets = {}
        date_facets = {}
        query_facets = {}
        facet_serializer_cls = view.get_facet_serializer_class()

        if view.lookup_sep == ":":
            raise AttributeError("The %(cls)s.lookup_sep attribute conflicts with the HaystackFacetFilter "
                                 "query parameter parser. Please choose another `lookup_sep` attribute "
                                 "for %(cls)s." % {"cls": view.__class__.__name__})

        fields = facet_serializer_cls.Meta.fields
        exclude = facet_serializer_cls.Meta.exclude
        field_options = facet_serializer_cls.Meta.field_options

        for field, options in kwargs.items():

            if field not in fields or field in exclude:
                continue

            field_options = merge_dict(field_options, {field: self.parse_field_options(view.lookup_sep, *options)})

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

    def build_geo_query(self, view, **kwargs):
        raise NotImplemented("GEO Queries are currently handled by subclassing BaseHaystackGEOSpatialFilter")

    def tokenize(self, stream, seperator):
        """
        Tokenizes a value into
        :param stream:
        :param seperator:
        :return:
        """
        for value in stream:
            for token in value.split(seperator):
                if token:
                    yield token.strip()

    def parse_field_options(self, lookup_sep, *options):
        """
        Parse the field options query string and return it as a dictionary.
        """
        defaults = {}
        for option in options:
            if isinstance(option, six.text_type):
                tokens = [token.strip() for token in option.split(lookup_sep)]

                for token in tokens:
                    if not len(token.split(":")) == 2:
                        warnings.warn("The %s token is not properly formatted. Tokens need to be "
                                      "formatted as 'token:value' pairs." % token)
                        continue

                    param, value = token.split(":")

                    if any([k == param for k in ("start_date", "end_date", "gap_amount")]):

                        if param in ("start_date", "end_date"):
                            value = parser.parse(value)

                        if param == "gap_amount":
                            value = int(value)

                    defaults[param] = value

        return defaults
