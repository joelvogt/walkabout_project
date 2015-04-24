# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'

from json import loads

import paho.mqtt.client as mqtt


DEF MQTT_SERVER = 'test.mosquitto.org'
DEF WALKABOUT_SERVER = 'localhost'
DEF WALKABOUT_MODULE = 'mqtt_producer'
DEF TASK = 'experiment'

cdef class FrameAction(object):
    """Action objects on frame should be callable and have a close function.
    Otherwise just use a  function"""
    cdef PluggableExperimentConsumer consumer
    # def __cinit__(self):


    def __call__(self, char *topic, frame):
        assert NotImplementedError

    def close(self):
        assert NotImplementedError

    def register_consumer(self, PluggableExperimentConsumer consumer):
        self.consumer = consumer

cdef class PluggableExperimentConsumer(object):
    cdef FrameAction action
    cdef char *label
    cdef str topic
    cdef object client
    cdef bint run_once

    def c__init__(self, experiment_label, FrameAction action):
        self.action = action
        self.label = experiment_label
        self.topic = '%(task)s/%(label)s' % dict(
            task=TASK,
            label=self.label)
        self.client = mqtt.Client()
        self.client.on_connect = lambda client, userdata, flags, rc: client.subscribe(self.topic)
        self.client.on_message = self.on_message
        self.run_once = False
        # if hasattr(action, 'register_consumer'):
        #     action.register_consumer(self)

    def __dealloc__(self):
        pass

    def on_message(self, object client, object userdata, buffer msg):
        cdef char *topic = msg.topic

        messages = loads(msg.payload.decode())
        for event in messages:
            if event == 'EOF':
                if hasattr(self.frame_action, 'close'):
                    self.frame_action.close()
                if self.run_once:
                    self.client.disconnect()
                break
            else:
                self.frame_action(topic, event)

