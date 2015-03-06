# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'

from walkabout.base.client import import_module

mqtt_producer = import_module('mqtt_producer', '137.138.79.116')

for i in range(10000):
    mqtt_producer.single('foo', 'hello fsadfdsafdsafdsaf', hostname='test.mosquitto.org', client_id='itsme')