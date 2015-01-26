# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'


def networked_function(buffered=False):
    def wrapper(func):
        networked_function.functions_registry.append((func, buffered))
        return func

    return wrapper


networked_function.functions_registry = []
