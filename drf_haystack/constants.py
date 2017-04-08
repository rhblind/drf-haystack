from django.conf import settings

DRF_HAYSTACK_NEGATION_KEYWORD = getattr(settings, "DRF_HAYSTACK_NEGATION_KEYWORD", "not")
GEO_SRID = getattr(settings, "GEO_SRID", 4326)
DRF_HAYSTACK_SPATIAL_QUERY_PARAM = getattr(settings, "DRF_HAYSTACK_SPATIAL_QUERY_PARAM", "from")
