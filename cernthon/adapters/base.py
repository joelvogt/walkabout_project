# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'


def function_adapter_mapper(func, adapter):
    def onCall(*args, **kwargs):
        return adapter(func(*args, **kwargs))

    return onCall