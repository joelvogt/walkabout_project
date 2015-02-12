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


def _process_wrapper(func, buffer_file, args_queue, tcp_socket, buffer_of_method_function, endpoint):
    fd = open(buffer_file)
    while True:
        try:
            size = args_queue.get(timeout=10)
            func(fd.read(size))
        except Empty:
            if buffer_of_method_function:
                print('sending rest')
                args = ((buffer_of_method_function,), {})
                func(endpoint.to_send(args))
            print('closing')
            tcp_socket.send(CLOSE_CONNECTION)
            print('exit sender')
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


class BufferedMethod(object):
    def __init__(self, func, buffer_size, endpoint, return_handler, tcp_socket):
        self._buffer_size = buffer_size
        self._args_queue = Queue()
        self._endpoint = endpoint
        self._buffer = deque()
        self._func = func
        self._current_buffer_size = 0
        self._tcp_socket = tcp_socket
        self._temp_file = tempfile.NamedTemporaryFile()
        self._network_func = Thread(target=_process_wrapper,
                                    args=(func,
                                          self._temp_file.name,
                                          self._args_queue, tcp_socket, self._buffer, self._endpoint))

        self._network_func.start()

        def return_value_listener(_return_handler, return_values):
            while True:
                remote_return_values = _return_handler()
                for return_value in remote_return_values:
                    if isinstance(remote_return_values, Exception):
                        raise return_value
                    else:
                        return_values.append(return_value)

                if remote_return_values == CLOSE_CONNECTION:
                    print('ending return handler')
                    break

        self.return_values = deque()
        self._return_handler = Thread(target=return_value_listener, args=(return_handler, self.return_values))
        self._return_handler.start()

    def __iter__(self):
        self._return_handler.join()
        return self.return_values.__iter__()

    def __call__(self, *args, **kwargs):
        arg_input = (args, kwargs)
        self._current_buffer_size += 1
        self._buffer.append(arg_input)
        print('debug 0')
        if self._current_buffer_size >= 100:
            print('debug 1')
            to_serial_args = ((self._buffer,), {})
            self._buffer = deque()
            self._current_buffer_size = 0
            serialized = self._endpoint.to_send(to_serial_args)
            size = len(serialized)
            self._temp_file.write(serialized)
            self._temp_file.flush()

            self._args_queue.put(size)

    def __del__(self):
        print('debug del')
        self._network_func.join()
        # if self._current_buffer_size > 0:
        # print('size +0')
        #     args = ((self._buffer,), {})
        #     self._func(self._endpoint.to_send(args))
        #     self._current_buffer_size = 0
        print('clsng')
        # self._tcp_socket.send(CLOSE_CONNECTION)
        self._return_handler.join()
        print('bue bye')


def remote_function(function_ref, tcp_client_socket, serialized_content):
    message = '%(header)s' \
              '%(delimiter)s' \
              '%(function_ref)s' \
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
                                     name,
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
        # self._tcp_client_socket.send(CLOSE_CONNECTION)
        self._tcp_client_socket.close()
