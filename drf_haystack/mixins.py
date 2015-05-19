# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.utils import six
from haystack.utils import Highlighter


class HighlighterMixin(object):
    """
    This mixin adds support for highlighting (the pure python
    version, not SearchQuerySet().highlight()). See Haystack docs
    for more info).
    """

    highlighter_class = Highlighter

    def get_highlighter(self):
        if not self.highlighter_class:
            raise ImproperlyConfigured(
                "%(cls)s is missing a highlighter_class. Define %(cls)s.highlighter_class, "
                "or override %(cls)s.get_highlighter()." %
                {"cls": self.__class__.__name__}
            )
        return self.highlighter_class

    def get_serializer_context(self):
        context = super(HighlighterMixin, self).get_serializer_context()
        words = " ".join(six.itervalues(self.request.GET))
        highlighter = self.get_highlighter()(words)
        if highlighter:
            context["highlighter"] = highlighter
        return context

