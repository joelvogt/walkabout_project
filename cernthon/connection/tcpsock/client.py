# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import functools
import socket
from threading import Thread
from Queue import Queue, Empty
from collections import deque
from atexit import register
import tempfile

from cernthon.helpers import datalib
from cernthon.connection import CLOSE_CONNECTION


BUFFER_SIZE = 1024

CLIENTS = [
    'default',
    'Jython',
    'CPython',
    'PyPy'
]


def _process_wrapper(func, buffer_file, args_queue):
    fd = open(buffer_file)
    while True:
        try:
            size = args_queue.get(timeout=1)
            func(fd.read(size))
        except Empty:
            break


class BufferedMethod(object):
    def __init__(self, func):
        self._args_queue = Queue()
        self._buffer = deque()
        self._func = func
        self._buffer_size = 0
        self._temp_file = tempfile.NamedTemporaryFile()
        self._network_func = Thread(target=_process_wrapper,
                                    args=(func,
                                          self._temp_file.name,
                                          self._args_queue))
        self._network_func.start()

    def __call__(self, *args, **kwargs):
        self._buffer.append((args, kwargs))
        self._buffer_size += 1
        if self._buffer_size >= BUFFER_SIZE:
            args = ((self._buffer,), {})
            serialized = datalib.serialize_data(args)
            self._buffer = deque()
            self._temp_file.write(serialized)
            self._temp_file.flush()
            self._buffer_size = 0
            size = len(serialized)
            self._args_queue.put(size)

    def __del__(self):
        self._network_func.join()
        if self._buffer_size > 0:
            args = ((self._buffer,), {})
            self._func(datalib.serialize_data(args))
            self._buffer_size = 0


def remote_function(function_ref, tcp_client_socket, buffer_size, serialized):
    message = '%(header)s' \
              '%(delimiter)s' \
              '%(function_ref)d' \
              '%(delimiter)s' \
              '%(message_length)d' \
              '%(delimiter)s' \
              '%(header_end)s' \
              '%(message)s' % \
              dict(
                  header=datalib.MESSAGE_HEADER,
                  function_ref=function_ref,
                  message_length=len(serialized),
                  message=serialized,
                  delimiter=datalib.HEADER_DELIMITER,
                  header_end=datalib.MESSAGE_HEADER_END)

    tcp_client_socket.send(message)
    return_values = datalib.deserialize_data(tcp_client_socket.recv(buffer_size))
    if isinstance(return_values, Exception):
        raise return_values
    else:
        return return_values


def serialized_arguments(func):
    def on_call(*args, **kwargs):
        return func(datalib.serialize_data((args, kwargs)))
    return on_call


class Client(object):
    def __init__(self, hostname, port, buffer_size, unbuffered_methods, buffered_methods=None):
        if not buffered_methods:
            buffered_methods = []
        self._methods_cache = {}
        self._server_address = (hostname, port)
        self._buffer_size = buffer_size
        self._last_method = None
        self._last_method_name = None
        self._buffered_methods = buffered_methods
        self._methods_registry = unbuffered_methods + buffered_methods
        self._tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_client_socket.connect(self._server_address)

    def __getattr__(self, name):
        if name not in self._methods_registry:
            raise AttributeError("Client side exception: \
            Remote 'module' doesn't have that function")
        if name != self._last_method_name:
            self._last_method_name = name
            func = functools.partial(remote_function,
                                     self._methods_registry.index(name),
                                     self._tcp_client_socket,
                                     self._buffer_size)
            if name in self._buffered_methods:
                self._last_method = BufferedMethod(func)
            else:
                self._last_method = serialized_arguments(func)
        return self._last_method

    def __del__(self):
        if self._last_method is not None:
            if hasattr(self._last_method, '__del__'):
                self._last_method.__del__()  # Jython won't call this destructor
            self._last_method = None
        self._tcp_client_socket.send(CLOSE_CONNECTION)
        self._tcp_client_socket.close()
