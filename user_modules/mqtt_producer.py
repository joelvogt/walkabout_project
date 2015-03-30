# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'

from paho.mqtt.publish import single, multiple

from walkabout.helpers.moduleslib import networked_function


networked_function(buffered=False)(single)

networked_function(buffered=False)(multiple)
