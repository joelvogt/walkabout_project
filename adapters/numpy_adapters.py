#-*- coding:utf-8 -*-
__author__ = u'Joël Vogt'

import numpy

def numpy_to_xmlrpc(value):
    def map_value(value):
        if type(value) == numpy.ndarray:
            return value.tolist()
        else:
            return value

    if type(value) in [list, tuple]:
        return map(map_value, value)
    return value