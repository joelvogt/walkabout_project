# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import functools
import socket

from helpers import datalib
from threading import Thread
from Queue import Queue


BUFFER_SIZE = 4096

CLIENTS = [
    'default',
    'Jython',
    'CPython',
    'PyPy'
]


class BufferedMethod(object):

    def __init__(self, func):
        # self._func = func
        self._args_queue = Queue()
        self._return_value = []
        def process_wrapper(func, return_value, args_queue):


            while True:
                item = args_queue.get()
                if item == 'EOF': break
                func(item)
                # return_value.append(func(item))
        self._network_func = Thread(target=process_wrapper, args=(func, self._return_value, self._args_queue))
        self._network_func.start()

    def __call__(self, *args, **kwargs):


        self._args_queue.put((args, kwargs))

        # if len(self._buffer) == BUFFER_SIZE:
        #     """Even without a return value, exceptions can be returned an forwarded"""
            # return_value = []
            # Thread(target=process_wrapper(self._func, return_value, self._buffer)).start()
            # ret = self._func(self._buffer)
            # ret = return_value.pop()
            # self._buffer = []
            # self._buffer_size = 0
            # return ret

    def __del__(self): # Workaround for Jython not calling the destructor

        if self._network_func.isAlive():
            print('end')
            self._args_queue.join()
            self._args_queue.put('EOF')
            print('else')
        # if self._buffer is not None:
        #     ret = self._func(self._buffer)
        #     self._buffer = None
        #     return ret


class SocketServerProxy(object):
    def __init__(self, hostname, port, buffer_size, unbuffered_methods, buffered_methods=[]):
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
        def remote_function(function_ref, tcpCliSock, server_address, buffer_size, *args, **kwargs):
            serialized = datalib.serialize_data((args, kwargs))
            message = '%(header)s%(delimiter)s%(function_ref)d%(delimiter)s%(message_length)d%(delimiter)s%(header_end)s%(message)s' % dict(
                header=datalib.MESSAGE_HEADER,
                function_ref=function_ref,
                message_length=len(serialized),
                message=serialized,
                delimiter=datalib.HEADER_DELIMITER,
                header_end=datalib.MESSAGE_HEADER_END)

            tcpCliSock.send(message)
            return_values = datalib.deserialize_data(tcpCliSock.recv(buffer_size))
            if isinstance(return_values, Exception):
                raise return_values
            else:
                return return_values


        if name != self._last_method_name:
            self._last_method_name = name
            func = functools.partial(remote_function, self._methods_registry.index(name), self._tcpCliSock,
                                     self._server_address, self._buffer_size)
            self._last_method = \
                BufferedMethod(func) \
                    if name in self._buffered_methods \
                    else func
        return self._last_method

    def __del__(self):
        if self._last_method is not None:
            self._last_method.__del__() # Jython won't call this destructor
            self._last_method = None
            self._tcpCliSock.close()