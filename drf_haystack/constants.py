from django.conf import settings

DRF_HAYSTACK_NEGATION_KEYWORD = getattr(settings, "DRF_HAYSTACK_NEGATION_KEYWORD", "not")
GEO_SRID = getattr(settings, "GEO_SRID", 4326)
