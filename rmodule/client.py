# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import functools
import socket
TEMP_FOLDER = 'var/tmp'
from helpers import datalib
from threading import Thread
from Queue import Queue, Empty
from collections import deque
from atexit import register
from tempfile import NamedTemporaryFile

import os, time

BUFFER_SIZE = 8192
TERMINATE_FUNCTION = 0
CONTINUE_FUNCTION = 1

CLIENTS = [
    'default',
    'Jython',
    'CPython',
    'PyPy'
]

parent_directory = '.'
for directory in TEMP_FOLDER.split('/'):
    directory = '%s/%s' % (parent_directory, directory)
    if not os._exists(directory):
        os.mkdir(directory)
        parent_directory = directory

def process_wrapper(func, args_queue):
    while True:
        try:
            size, file_name= args_queue.get(timeout=1)
            fd = open(file_name, 'r')
            func(fd.read(size))
            fd.close()
        except Empty:

            break


class BufferedMethod(object):

    def __init__(self, func):
        self._args_queue = Queue()
        self._buffer = deque()
        self._func = func
        self._buffer_size = 0
        self._network_func = Thread(target=process_wrapper, args=(func, self._args_queue))
        self._network_func.start()

    def __call__(self, *args, **kwargs):
        self._buffer.append((args, kwargs))
        self._buffer_size += 1
        if self._buffer_size >= BUFFER_SIZE:
            args = ((self._buffer,), {})
            serialized = datalib.serialize_data(args)
            self._buffer = deque()
            file_name = '%s/buffer-%f.tmp' % (TEMP_FOLDER, time.time())
            fd = open(file_name, 'w')
            fd.write(serialized)
            fd.flush()
            fd.close()
            self._buffer_size = 0
            size = len(serialized)
            self._args_queue.put((size, file_name))

    def __del__(self):
        self._network_func.join()
        if self._buffer_size > 0:
            args = ((self._buffer,), {})
            self._func(datalib.serialize_data(args))
        for temp_file in filter(lambda x: x[-3:] == 'tmp', os.listdir(TEMP_FOLDER)):
            os.remove('%s/%s' % (TEMP_FOLDER, temp_file))



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
        register(self.__del__) # Jython won't call this destructor


    def __getattr__(self, name):
        def remote_function(function_ref, tcpCliSock, server_address, buffer_size, serialized):

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
            if name in self._buffered_methods:
                self._last_method = BufferedMethod(func)
            else:
                def serliazed_arguments(func):
                    def onCall(*args, **kwargs):
                        return func(datalib.serialize_data((args, kwargs)))
                    return onCall
                self._last_method = serliazed_arguments(func)
        return self._last_method

    def __del__(self):
        if self._last_method is not None:
            if hasattr(self._last_method,'__del__'):
                self._last_method.__del__() # Jython won't call this destructor
            self._last_method = None
            self._tcpCliSock.close()