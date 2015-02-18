# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'

import numpy


def map_value(_value):
    if type(_value) == numpy.ndarray:
        return _value.tolist()
    else:
        return _value


def numpy_to_jython(func):
    def on_call(*args, **kwargs):
        result = func(*args, **kwargs)
        if type(result) in [list, tuple]:
            return map(map_value, result)
        return result

    return on_call