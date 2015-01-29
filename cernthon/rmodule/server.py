# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import socket
import multiprocessing
import warnings


# from cernthon.adapters import numpy_adapters as npa
from cernthon.adapters import base
from cernthon.helpers import datalib


DEFAULT_ADAPTERS = []
TIMEOUT = 10


def _function_process(tcp_client_socket, buffer_size, remote_functions):
    input_buffer = None
    total_data_size = 0
    remote_function = None
    """ return_value == -1 if no function was called.
    None can be returned by functions without explicit return value"""
    return_value = -1
    frame = None
    is_used_by_client = True
    while is_used_by_client:
        while is_used_by_client:

            message = tcp_client_socket.recv(buffer_size)
            if CLOSE_CONNECTION in message:
                print('Connection Timeout')
                print(len(frame))
                break

            if not message:
                is_used_by_client = False
                return_value = -1
                break
            if not remote_function:
                if message[:3] != datalib.MESSAGE_HEADER:
                    return_value = ReferenceError(
                        'Message does not contain header information and a function reference')
                    frame = None
                    break
                header, message = message.split('%(delimiter)s%(header_end)s' % dict(
                    delimiter=datalib.HEADER_DELIMITER,
                    header_end=datalib.MESSAGE_HEADER_END))
                header, function, message_length = header.split(datalib.HEADER_DELIMITER)
                try:
                    remote_function = remote_functions[int(function)]
                    total_data_size = int(message_length)
                    input_buffer = datalib.InputStreamBuffer(message)
                except IndexError:
                    return_value = AttributeError("Server side exception: \
                    Remote module doesn't have that function")
                    frame = None
                    break
            else:
                input_buffer.extend(message)
            if total_data_size < input_buffer.size:
                return_value = OverflowError(
                    'Server side exception: \
                    The size {} is longer than \
                    the expected message size {}'.format(
                        input_buffer.size,
                        total_data_size))
            elif total_data_size == input_buffer.size:
                frame = input_buffer[0:input_buffer.size]
            else:
                continue
            break
        if frame:
            print('process frame')
            args, kwargs = datalib.deserialize_data(frame)
            try:
                return_value = remote_function(*args, **kwargs)
            except Exception as e:
                return_value = e
        if return_value != -1:
            print('process return value')
            tcp_client_socket.send(datalib.serialize_data(return_value))
            remote_function = None
    tcp_client_socket.close()


class SocketModuleBinder(object):
    def __init__(self, hostname, port, buffer_size=datalib.NETWORK_BUFFER_SIZE, adapters=DEFAULT_ADAPTERS):
        self._hostname = hostname
        self._port = port
        self._buffer_size = buffer_size
        self._adapters = adapters
        self._remote_functions = []
        self._tcpSerSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcpSerSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._tcpSerSock.bind((self._hostname, self._port))
        self._tcpSerSock.listen(5)
        self._ready = True
        self._buffered_methods = []
        self._unbuffered_methods = []

    def _register_function(self, func, name):
        self._remote_functions.append(func)

    def __del__(self):
        self._tcpSerSock.close()

    def run(self):
        while True:
            tcp_client_socket, _ = self._tcpSerSock.accept()
            p = multiprocessing.Process(target=_function_process,
                                        args=(tcp_client_socket, self._buffer_size, self._remote_functions))
            p.start()

    def connection_information(self):
        return self._hostname, \
               self._port, \
               self._buffer_size, \
               dict(
                   unbuffered_methods=self._unbuffered_methods,
                   buffered_methods=self._buffered_methods
               )

    def __call__(self, buffered_func, buffered=False):
        def buffered_function(func):
            def on_call(params):
                return [func(*args, **kwargs) for args, kwargs in params]

            return on_call

        networked_func = buffered_func
        for adapter in self._adapters:
            networked_func = base.function_adapter_mapper(networked_func, adapter)
        if buffered:
            self._buffered_methods.append(buffered_func.__name__)
            networked_func = buffered_function(networked_func)
        else:
            self._unbuffered_methods.append(buffered_func.__name__)
        self._register_function(networked_func, name=buffered_func.__name__)
