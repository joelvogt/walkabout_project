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
    f_args_queue_get = args_queue.get
    input_buffer = deque()
    f_buffer_popleft = input_buffer.popleft
    f_buffer_append = input_buffer.append
    f_endpoint_to_send = endpoint.to_send
    f_tcp_socket_send = tcp_socket.send
    buffer_size = 0
    buffer_limit = 50
    is_alive = True

    while is_alive:
        try:

            args = f_args_queue_get(timeout=0.01)
            f_buffer_append(args)
            buffer_size += 1
        except Empty:
            buffer_limit = buffer_size
            is_alive = False

        if buffer_size == buffer_limit:
            to_serial_args = ((map(lambda x: f_buffer_popleft(), range(buffer_size)),), {})
            buffer_size = 0
            func(tcp_socket, f_endpoint_to_send(to_serial_args))
    f_tcp_socket_send(FLUSH_BUFFER_REQUEST)


def handle_return_value(buffer_size, endpoint, tcp_client_socket, is_buffering):
    f_str_join = ''.join

    # f_tcp_socket_recv = tcp_client_socket.recv
    # f_tcp_client_socket_send = tcp_client_socket.send
    #
    # f_endpoint_to_send = endpoint.to_send
    # f_endpoint_to_receive = endpoint.to_receive
    frame = None
    next_frame = None
    return_values = deque()
    receiving = True
    f_tcp_socket_recv = tcp_client_socket.recv
    f_return_values_append = return_values.append
    f_endpoint_to_receive = endpoint.to_receive
    while True:
        if receiving:
            message = f_tcp_socket_recv(buffer_size)
        else:
            message = next_frame
            next_frame = None

        if next_frame:
            message = f_str_join([next_frame, message])
            next_frame = None
        if message[-3:] == FLUSH_BUFFER_REQUEST:
            receiving = False
        # if len(message) < 3:
        # continue
        if message[:3] == MESSAGE_HEADER:
            function_ref, total_data_size, frame = get_header_from_message(message)
        elif message == FLUSH_BUFFER_REQUEST:

            break
        if len(frame) > total_data_size:
            next_frame = frame[total_data_size:]
            frame = frame[:total_data_size]
        elif len(frame) < total_data_size:

            next_frame = frame
        if len(frame) == total_data_size:
            f_return_values_append(f_endpoint_to_receive(frame))
        if not next_frame and not is_buffering:
            break
    return receiving, return_values


def return_value_listener(_return_handler, _tcp_socket, return_values, is_buffering):
    return_values_extend = return_values.extend
    while True:
        receiving, remote_return_value = _return_handler(_tcp_socket, is_buffering)
        if not remote_return_value:
            break
        if remote_return_value == -1:
            break
        if isinstance(remote_return_value, Exception):
            raise remote_return_value
        if len(remote_return_value) > 1:
            for i in remote_return_value:
                return_values_extend(i)
        if not receiving:
            break


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
        _, return_values = self._return_handler(self._tcp_socket, False)
        return return_values[0]

    def is_alive(self):
        return self._is_alive


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
                                      args=(return_handler, tcp_socket, self.return_values, True))
        self._return_handler.start()

    def is_alive(self):
        print('is alive')
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
