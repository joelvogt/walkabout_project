# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import sys

if '/Users/joelvogt/PyCharmProjects/walkabout_project/' not in sys.path:
    sys.path.append('/Users/joelvogt/PyCharmProjects/walkabout_project/')

from walkabout.base.client import import_module

mqtt_producer = import_module('mqtt_producer')

for i in range(100):
    mqtt_producer.single('foo', hostname='137.138.79.116')