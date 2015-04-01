# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
from collections import deque
from json import dumps, loads

from walkabout.base.client import import_module


class ExperimentProducer(object):
    mqtt_server = 'test.mosquitto.org'
    walkabout_server = 'localhost'
    walkabout_module = 'mqtt_producer'
    task = 'experiment'

    def __init__(self, experiment_label, timerate):
        self.mqtt_producer = import_module(ExperimentProducer.walkabout_module)
        self.label = experiment_label
        self.timerate = timerate
        self.frame_buffer = deque()
        self.frame_id = -1
        self.header = None
        self.topic = '%(task)s/%(label)s' % dict(
            task=ExperimentProducer.task,
            label=self.label)

    def send_frames(self):
        f_frame_buffer_pop_left = self.frame_buffer.popleft
        message = dumps([f_frame_buffer_pop_left() for i in range(len(self.frame_buffer))])
        self.mqtt_producer.single(self.topic,
                                  message,
                                  hostname=ExperimentProducer.mqtt_server)

    def add_frame(self, raw_event):
        event = raw_event.split()
        if len(event) == 0:
            event = [raw_event]
        first_item = event[0]

        if self.frame_id == -1:  # Header data, event data starts at 0
            self.frame_buffer.append(event)
            if ord(first_item[0]) >= ord('0') and ord(first_item[0]) <= ord(
                    '9'):  # it's a event number. Done processing the header
                self.frame_id = int(first_item[0])
                self.header = self.frame_buffer[-2]
                self.frame_buffer.clear()
        else:
            event_object = dict(zip(self.header, event))
            self.frame_buffer.append(event_object)
            if self.frame_id != first_item and (int(first_item) % self.timerate) == 0:
                self.frame_id = first_item
                self.send_frames()

    def close(self):
        self.frame_buffer.append(b'EOF')
        self.send_frames()


try:
    import paho.mqtt.client as mqtt

    class ExperimentConsumer(object):
        mqtt_server = 'test.mosquitto.org'
        task = 'experiment'

        def __init__(self, experiment_label, frame_action):
            self.frame_action = frame_action
            self.label = experiment_label
            self.topic = '%(task)s/%(label)s' % dict(
                task=ExperimentConsumer.task,
                label=self.label)
            self.client = mqtt.Client()
            self.client.on_connect = lambda client, userdata, flags, rc: client.subscribe(self.topic)
            self.client.on_message = self.on_message
            self.run_once = False
            if hasattr(frame_action, 'register_consumer'):
                frame_action.register_consumer(self)

        def on_message(self, client, userdata, msg):
            topic = msg.topic
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

        def listen(self, run_once=False):
            self.run_once = run_once
            self.client.connect(ExperimentConsumer.mqtt_server)
            self.client.loop_forever()


    class FrameAction(object):
        """Action objects on frame should be callable and have a close function.
        Otherwise just use a  function"""

        def __call__(self, topic, frame):
            assert NotImplementedError

        def close(self):
            assert NotImplementedError

        def register_consumer(self, consumer):
            self.consumer = consumer
except ImportError:
    pass

try:
    import cython

    class PluggaleExperimentProducer(ExperimentProducer):
        def __init__(self, experiment_label, frame_action):
            ExperimentProducer.__init__(self, experiment_label, frame_action)



except ImportError:
    pass