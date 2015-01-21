# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import functools
import socket
import weakref

from helpers import datalib

BUFFER_SIZE = 8192

CLIENTS = [
    'default',
    'Jython',
    'CPython',
    'PyPy'
]



class SocketServerProxy(object):
    def __init__(self, hostname, port, buffer_size, unbuffered_methods, buffered_methods = []):
        self._methods_cache = {}
        self._server_address = (hostname, port)
        self._buffer_size = buffer_size
        self._last_method = None
        self._last_method_name = None
        self._buffered_methods = buffered_methods
        self._methods_registry = unbuffered_methods + buffered_methods
        self._tcpCliSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcpCliSock.connect(self._server_address)

    def __getattr__(self, name):
        def remote_function(function_ref, tcpCliSock, server_address, buffer_size,  *args, **kwargs):
            serialized = datalib.serialize_data((args, kwargs))
            message = '%(header)s%(delimiter)s%(function_ref)d%(delimiter)s%(message_length)d%(delimiter)s%(header_end)s%(message)s' % dict(
                header=datalib.MESSAGE_HEADER,
                function_ref=function_ref,
                message_length=len(serialized),
                message=serialized,
                delimiter=datalib.HEADER_DELIMITER,
                header_end = datalib.MESSAGE_HEADER_END)

            tcpCliSock.send(message)
            return_values = datalib.deserialize_data(tcpCliSock.recv(buffer_size))
            if isinstance(return_values, Exception):
                raise return_values
            else:
                return return_values

        class BufferedMethod(object):

            def __init__(self, func):
                self._buffer = []
                self._func = func

            def __call__(self, *args, **kwargs):
                self._buffer.append((args, kwargs))
                if len(self._buffer) == BUFFER_SIZE:
                    func(self._buffer)
                    print(len(self._buffer))
                    self._buffer = []
                    self._buffer_size = 0

            def __del__(self):
                self._func(self._buffer)

        if name is not self._last_method_name:
            self._last_method_name = name
            func = functools.partial(remote_function, self._methods_registry.index(name), self._tcpCliSock, self._server_address, self._buffer_size)
            self._last_method  = \
                BufferedMethod(func) \
                    if name in self._buffered_methods \
                    else func
        return self._last_method

    def __del__(self):
        del self._last_method
        self._tcpCliSock.close()