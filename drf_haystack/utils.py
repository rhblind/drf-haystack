# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from copy import deepcopy
from django.utils import six


def merge_dict(a, b):
    """
    Recursively merges and returns dict a with dict b.
    Any list values will be combined and returned sorted.

    :param a: dictionary object
    :param b: dictionary object
    :return: merged dictionary object
    """

    if not isinstance(b, dict):
        return b

    result = deepcopy(a)
    for key, val in six.iteritems(b):
        if key in result and isinstance(result[key], dict):
            result[key] = merge_dict(result[key], val)
        elif key in result and isinstance(result[key], list):
            result[key] = sorted(list(set(val) | set(result[key])))
        else:
            result[key] = deepcopy(val)

    return result
