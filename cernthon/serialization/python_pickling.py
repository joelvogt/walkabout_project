# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import cPickle
import sys
import functools

if sys.version_info[:3] > (2, 7, 0):
    serialize = functools.partial(cPickle.dumps, protocol=2)
else:
    serialize = cPickle.dumps

deserialize = cPickle.loads