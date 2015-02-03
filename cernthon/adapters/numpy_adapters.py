# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'

import numpy


def numpy_to_jython(value):
    def map_value(_value):
        if type(_value) == numpy.ndarray:
            return _value.tolist()
        else:
            return _value

    if type(value) in [list, tuple]:
        return map(map_value, value)
    return value