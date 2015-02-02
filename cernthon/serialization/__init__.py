# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'


class SerializationEndpoint(object):

    def __init__(self, send_func, receive_func, adapters=[]):
        self._send_func = send_func
        self._receive_func = receive_func
        self._adapters = adapters

    def to_send(self, *args, **kwargs):
        return self._send_func(*args, **kwargs)

    def to_receive(self, *args, **kwargs):
        return self._receive_func(*args, **kwargs)