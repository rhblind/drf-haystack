from django.conf import settings

DRF_HAYSTACK_NEGATION_KEYWORD = getattr(settings, "DRF_HAYSTACK_NEGATION_KEYWORD", "not")