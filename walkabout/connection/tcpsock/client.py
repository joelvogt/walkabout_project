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


def _process_wrapper(func, buffer_file, args_queue, tcp_socket):
    fd = open(buffer_file)
    while True:
        try:
            size = args_queue.get(timeout=10)
            func(fd.read(size))
        except Empty:
            print('ending connection')
            tcp_socket.send(CLOSE_CONNECTION)
            break


def handle_return_value(tcp_client_socket, buffer_size, endpoint):
    return_values = endpoint.to_receive(tcp_client_socket.recv(buffer_size))
    if isinstance(return_values, Exception):
        raise return_values
    else:
        return return_values


def serialized_arguments(func, return_handler, endpoint):
    def on_call(*args, **kwargs):
        func(endpoint.to_send((args, kwargs)))
        return return_handler()

    return on_call


# TODO bug fixing...
class BufferedMethod(object):
    def __init__(self, func, buffer_size, endpoint, return_handler, tcp_socket):
        self._buffer_size = buffer_size
        self._args_queue = Queue()
        self._endpoint = endpoint
        self._buffer = deque()
        self._func = func
        self._current_buffer_size = 0

        self._temp_file = tempfile.NamedTemporaryFile()
        self._network_func = Thread(target=_process_wrapper,
                                    args=(func,
                                          self._temp_file.name,
                                          self._args_queue, tcp_socket))

        self._network_func.start()

        def return_value_listener(_return_handler):
            while True:
                res = _return_handler()
                if res == CLOSE_CONNECTION:
                    print('return ends connection')
                    break

        self._return_handler = Thread(target=return_value_listener, args=(return_handler,))
        self._return_handler.start()

    def __call__(self, *args, **kwargs):
        arg_input = (args, kwargs)
        self._current_buffer_size += 1  # sys.getsizeof(arg_input)
        # print(sys.getsizeof(arg_input))
        self._buffer.append(arg_input)
        if self._current_buffer_size >= 50:
            args = ((self._buffer,), {})
            self._buffer = deque()
            self._current_buffer_size = 0
            serialized = self._endpoint.to_send(args)
            size = len(serialized)
            self._temp_file.write(serialized)
            self._temp_file.flush()

            self._args_queue.put(size)

    def __del__(self):
        print('del buffer')
        self._network_func.join()
        if self._current_buffer_size > 0:
            print('sizd above 0')
            args = ((self._buffer,), {})
            self._func(self._endpoint.to_send(args))
            self._current_buffer_size = 0
        self._return_handler.join()


def remote_function(function_ref, tcp_client_socket, serialized_content):
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
                                     self._tcp_client_socket)
            return_handler = functools.partial(handle_return_value,
                                               self._tcp_client_socket,
                                               self._buffer_size,
                                               self._endpoint)

            if name in self._buffered_methods:
                self._last_method = BufferedMethod(func, self._buffer_size, self._endpoint, return_handler,
                                                   self._tcp_client_socket)
            else:

                self._last_method = serialized_arguments(func, return_handler, self._endpoint)
        return self._last_method

    def __del__(self):
        if self._last_method is not None:
            if hasattr(self._last_method, '__del__'):
                self._last_method.__del__()  # Jython won't call this destructor
            self._last_method = None
        self._tcp_client_socket.send(CLOSE_CONNECTION)
        self._tcp_client_socket.close()
