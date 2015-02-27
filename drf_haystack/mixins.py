# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from haystack.utils import Highlighter


class HighlighterMixin(object):
    """
    Adds support for highlighting.
    """

    highlighter_class = Highlighter

    def get_highlighter(self):
        if not self.highlighter_class:
            pass
        return self.highlighter_class

    def get_serializer_context(self):
        context = super(HighlighterMixin, self).get_serializer_context()
        return context

