# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import functools
import socket
from threading import Thread
from Queue import Queue, Empty
from collections import deque
import tempfile

from walkabout.connection.tcpsock import HEADER_DELIMITER, MESSAGE_HEADER_END, MESSAGE_HEADER
from walkabout.connection import CLOSE_CONNECTION


def _process_wrapper(func, buffer_file, args_queue):
    fd = open(buffer_file)
    while True:
        try:
            size = args_queue.get(timeout=1)
            func(fd.read(size))
        except Empty:
            break


class BufferedMethod(object):
    def __init__(self, func, buffer_size, endpoint):
        self._buffer_size = buffer_size * 100
        self._args_queue = Queue()
        self._endpoint = endpoint
        self._buffer = deque()
        self._func = func
        self._current_buffer_size = 0
        self._temp_file = tempfile.NamedTemporaryFile()
        self._network_func = Thread(target=_process_wrapper,
                                    args=(func,
                                          self._temp_file.name,
                                          self._args_queue))
        self._network_func.start()

    def __call__(self, *args, **kwargs):
        self._buffer.append((args, kwargs))

        self._current_buffer_size += 1
        if self._current_buffer_size >= self._current_buffer_size:
            # args = ((self._buffer), {})
            serialized = self._endpoint.to_send(self._buffer)
            self._buffer = deque()
            self._temp_file.write(serialized)
            self._temp_file.flush()
            self._current_buffer_size = 0
            size = len(serialized)
            self._args_queue.put(size)

    def __del__(self):
        self._network_func.join()
        if self._current_buffer_size > 0:
            args = ((self._buffer,), {})
            self._func(self._endpoint.to_send(self))
            self._current_buffer_size = 0


def remote_function(function_ref, tcp_client_socket, buffer_size, endpoint, serialized_content):
    message = '%(header)s' \
              '%(delimiter)s' \
              '%(function_ref)d' \
              '%(delimiter)s' \
              '%(message_length)d' \
              '%(delimiter)s' \
              '%(header_end)s' \
              '%(message)s' % \
              dict(
                  header=MESSAGE_HEADER,
                  function_ref=function_ref,
                  message_length=len(serialized_content),
                  message=serialized_content,
                  delimiter=HEADER_DELIMITER,
                  header_end=MESSAGE_HEADER_END)

    tcp_client_socket.send(message)
    return_values = endpoint.to_receive(tcp_client_socket.recv(buffer_size))
    if isinstance(return_values, Exception):
        raise return_values
    else:
        return return_values


def serialized_arguments(func, endpoint):
    def on_call(*args, **kwargs):
        return func(endpoint.to_send((args, kwargs)))

    return on_call


class Client(object):
    def __init__(self, server_socket, buffer_size, unbuffered_methods, buffered_methods, endpoint):
        self._methods_cache = {}
        self._server_socket = tuple(server_socket)
        self._buffer_size = buffer_size
        self._endpoint = endpoint
        self._last_method = None
        self._last_method_name = None
        self._buffered_methods = buffered_methods
        self._methods_registry = unbuffered_methods + buffered_methods
        self._tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_client_socket.connect(self._server_socket)

    def __getattr__(self, name):
        if name not in self._methods_registry:
            raise AttributeError("Client side exception: \
            Remote 'module' doesn't have that function")
        if name != self._last_method_name:
            self._last_method_name = name
            func = functools.partial(remote_function,
                                     self._methods_registry.index(name),
                                     self._tcp_client_socket,
                                     self._buffer_size,
                                     self._endpoint)
            if name in self._buffered_methods:
                self._last_method = BufferedMethod(func, self._buffer_size, self._endpoint)
            else:
                self._last_method = serialized_arguments(func, self._endpoint)
        return self._last_method

    def __del__(self):
        if self._last_method is not None:
            if hasattr(self._last_method, '__del__'):
                self._last_method.__del__()  # Jython won't call this destructor
            self._last_method = None
        self._tcp_client_socket.send(CLOSE_CONNECTION)
        self._tcp_client_socket.close()
