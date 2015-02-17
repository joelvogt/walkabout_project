# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import functools
import socket
from threading import Thread
from Queue import Queue, Empty
from collections import deque
import time

from walkabout.connection.tcpsock import HEADER_DELIMITER, MESSAGE_HEADER_END, MESSAGE_HEADER, get_header_from_message
from walkabout.connection import CLOSE_CONNECTION, FLUSH_BUFFER_REQUEST


def input_data_handler(func, args_queue, tcp_socket, endpoint):
    buffer = deque()
    buffer_size = 0
    buffer_limit = 10
    is_alive = True

    while is_alive:
        try:

            args = args_queue.get(timeout=3)
            buffer_size += 1
        except Empty:
            print('timeout')
            buffer_limit = buffer_size
            is_alive = False
        buffer.append(args)
        if buffer_size == buffer_limit:
            to_serial_args = (([buffer.popleft() for i in range(buffer_size)],), {})
            buffer_size = 0
            func(tcp_socket, endpoint.to_send(to_serial_args))
    print('exiting')
    tcp_socket.send(FLUSH_BUFFER_REQUEST)


def handle_return_value(buffer_size, endpoint, tcp_client_socket):
    frame = None
    next_frame = None
    return_values = []
    message = None
    while True:
        message = tcp_client_socket.recv(buffer_size)
        print(message)
        if len(message) == 3:
            if message == FLUSH_BUFFER_REQUEST:
                break
        if next_frame:
            message = ''.joing([next_frame, message])
            next_frame = None
        if len(message) < 3:
            print(message)
            continue
        function_ref, total_data_size, frame = get_header_from_message(message)
        if len(frame) > total_data_size:
            next_frame = frame[total_data_size:]
            frame = frame[:total_data_size]
        if len(frame) == total_data_size:
            return_values.append(frame)
            frame = None
        if len(frame) < total_data_size:
            next_frame = frame
    print(return_values)
    return return_values


    if message[-3:] == FLUSH_BUFFER_REQUEST:  # TODO write return value handler for buffered functions
        print('flush request')
        return -1
    if message == CLOSE_CONNECTION:
        return -1

    return_values = endpoint.to_receive(message)
    if isinstance(return_values, Exception):
        raise return_values
    else:
        return return_values


def return_value_listener(_return_handler, _tcp_socket, return_values):
    while True:
        remote_return_value = _return_handler(_tcp_socket)
        if remote_return_value == -1:
            break

        if isinstance(remote_return_value, Exception):
            raise remote_return_value

        return_values.append(remote_return_value)


class UnbufferedMethod(object):
    def __init__(self, func, tcp_socket, return_handler, endpoint):
        self._endpoint = endpoint
        self._func = func
        self._tcp_socket = tcp_socket
        self._return_handler = return_handler
        self._is_alive = True

    def __call__(self, *args, **kwargs):
        self._func(self._tcp_socket, self._endpoint.to_send((args, kwargs)))
        self._is_alive = False
        return self._return_handler(self._tcp_socket)

    def is_alive(self):
        return self._is_alive


def unbuffered_method(func, tcp_socket, return_handler, endpoint):
    def on_call(*args, **kwargs):
        func(tcp_socket, endpoint.to_send((args, kwargs)))
        return return_handler(tcp_socket)

    return on_call


class BufferedMethod(object):
    def __init__(self, func, buffer_size, endpoint, return_handler, tcp_socket):
        self._buffer_size = buffer_size
        self._args_queue = Queue()
        self._endpoint = endpoint
        self._buffer = deque()
        self._func = func
        self._tcp_socket = tcp_socket
        self._network_func = Thread(target=input_data_handler,
                                    args=(func,
                                          self._args_queue, tcp_socket, endpoint))

        self._network_func.start()
        self.return_values = deque()
        self._return_handler = Thread(target=return_value_listener,
                                      args=(return_handler, tcp_socket, self.return_values))
        self._return_handler.start()

    def is_alive(self):
        return self._return_handler.isAlive() or self._network_func.isAlive()

    def __iter__(self):
        self._return_handler.join()
        return self.return_values.__iter__()

    def __call__(self, *args, **kwargs):
        self._args_queue.put((args, kwargs))

    def __del__(self):
        self._network_func.join()
        self._return_handler.join()


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
        self._server_socket = tuple(server_socket)
        self._buffer_size = buffer_size
        self._endpoint = endpoint
        self._last_method = None
        self._last_method_name = None
        self._buffered_methods = buffered_methods
        self._methods_registry = unbuffered_methods + buffered_methods
        self._tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_socket.connect(self._server_socket)

    def __getattr__(self, name):
        if name not in self._methods_registry:
            raise AttributeError("Client side exception: \
            Remote 'module' doesn't contain the function %s" % name)
        if name != self._last_method_name:
            self._last_method_name = name
            func = functools.partial(remote_function,
                                     name)
            return_handler = functools.partial(handle_return_value,
                                               self._buffer_size,
                                               self._endpoint)

            """wait until the buffered method has transmitted all the data and collected the return values"""
            while self._last_method is not None and self._last_method.is_alive():
                time.sleep(0.5)
            del self._last_method
            if name in self._buffered_methods:
                self._last_method = BufferedMethod(func, self._buffer_size, self._endpoint, return_handler,
                                                   self._tcp_socket)
            else:

                self._last_method = UnbufferedMethod(func, self._tcp_socket, return_handler, self._endpoint)

        return self._last_method

    def __del__(self):
        if self._last_method is not None:
            if hasattr(self._last_method, '__del__'):
                self._last_method.__del__()  # Jython won't call this destructor
            self._last_method = None
        self._tcp_socket.send(CLOSE_CONNECTION)
        self._tcp_socket.close()
