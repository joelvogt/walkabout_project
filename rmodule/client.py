# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import functools
import socket

from helpers import datalib


CLIENTS = [
    'default',
    'Jython',
    'CPython',
    'PyPy'
]



class SocketServerProxy(object):
    def __init__(self, hostname, port, buffer_size, unbuffered_methods, buffered_methods = [], buffer_limit=512):
        self._methods_cache = {}
        self._server_address = (hostname, port)
        self._buffer_size = buffer_size
        self._last_method = None
        self._buffer_limit = buffer_limit
        self._buffered_methods = buffered_methods
        self._methods_registry = unbuffered_methods + buffered_methods
        self._tcpCliSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcpCliSock.connect(self._server_address)

    def _flush_method(self, name):
        flush_func = self._methods_cache[name]
        flush_func.buffer_size = self._buffer_limit - 1
        flush_func(flush_func.buffer.pop())

    def __getattr__(self, name):
        def remote_function(function_ref, tcpCliSock, server_address, buffer_size,  *args, **kwargs):
            serialized = datalib.serialize_data((args, kwargs))
            message = '%s||%d||%d||%s' % (datalib.MESSAGE_HEADER, function_ref, len(serialized), serialized)
            tcpCliSock.send(message)
            return_values = datalib.deserialize_data(tcpCliSock.recv(self._buffer_size))
            if isinstance(return_values, Exception):
                raise return_values
            else:
                return return_values

        def wrapper(func):
            def onCall(*args, **kwargs):
                onCall.buffer.append((args, kwargs))
                onCall.buffer_size += 1
                if onCall.buffer_size == self._buffer_limit:
                    res = func(onCall.buffer)
                    onCall.buffer = []
                    onCall.buffer_size = 0
                    return res
            onCall.buffer = []
            onCall.buffer_size = 0
            return onCall
        if name not in self._methods_cache:
            func = functools.partial(remote_function, self._methods_registry.index(name), self._tcpCliSock, self._server_address, self._buffer_size)
            self._methods_cache[name] = \
                wrapper(func) \
                    if name in self._buffered_methods \
                    else func
        if name != self._last_method and name in self._buffered_methods:
            self._flush_method(name)
        self._last_method = name
        return self._methods_cache[name]

    def __del__(self):
        self._tcpCliSock.close()
        if self._methods_cache:
            map(self._flush_method, filter(lambda x: self._methods_cache[x].buffer_size > 0, self._buffered_methods))