# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
from walkabout.base.client import import_module
from collections import deque
from functools import partial
from json import dumps


class WalkaboutExperiment(object):
    mqtt_server = 'test.mosquitto.org'
    walkabout_server = 'localhost'
    walkabout_module = 'mqtt_producer'
    task = 'experiment'

    def __init__(self, experiment_label, frame_set_size):
        self.mqtt_producer = import_module(WalkaboutExperiment.walkabout_module)
        self.label = experiment_label
        self.frame_set_size = frame_set_size
        self.frame_buffer = deque()
        self.frame_id = -1
        self.topic = '%(task)s/%(label)s' % dict(
            task=WalkaboutExperiment.task,
            label=self.label)


    def send_frames(self):
        f_frame_buffer_pop_left = self.frame_buffer.popleft
        message = dumps([f_frame_buffer_pop_left() for i in range(len(self.frame_buffer))])

        self.mqtt_producer.single(self.topic, message,
                                  hostname=WalkaboutExperiment.mqtt_server)

    def add_frame(self, raw_frame):
        frame = raw_frame.split()
        if len(frame) == 0:
            frame = [raw_frame]
        self.frame_buffer.append(frame)
        first_item = frame[0]

        if self.frame_id == -1: #Header data, frame data starts at 0
            if ord(first_item[0]) >= ord('0') and ord(first_item[0]) <= ord('9'): #it's a frame number. Done processing the header
                self.frame_id = int(first_item[0])
        elif self.frame_id != first_item and (int(first_item) % self.frame_set_size) == 0:
            print(first_item)
            self.frame_id = first_item
            self.send_frames()

    def close(self):
        self.frame_buffer.append(b'EOF')
        self.send_frames()


fd = open('/Volumes/walkabout/milanodata.txt')
w = WalkaboutExperiment('testexp', 160)
for frame in fd.readlines():
    w.add_frame(frame)
w.close()
