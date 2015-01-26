# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import socket
import multiprocessing

from cernthon.adapters import numpy_adapters as npa
from cernthon.adapters import base
from cernthon.helpers import datalib


DEFAULT_ADAPTERS = [npa.numpy_to_jython]


class RemoteModuleBinder(object):
    def __init__(self, hostname, port, buffer_size):
        self._buffered_methods = []
        self._unbuffered_methods = []
        self._hostname = hostname
        self._port = port
        self._buffer_size = buffer_size

    def connection_information(self):
        return self._hostname, \
               self._port, \
               self._buffer_size, \
               dict(
                   unbuffered_methods=self._unbuffered_methods,
                   buffered_methods=self._buffered_methods
               )

    def _register_function(self, func, name):
        raise NotImplementedError

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


class SocketModuleBinder(RemoteModuleBinder):
    def __init__(self, hostname, port, buffer_size=datalib.DEFAULT_BUFFER_SIZE, adapters=DEFAULT_ADAPTERS):
        RemoteModuleBinder.__init__(self, hostname, port, buffer_size)
        self._adapters = adapters
        self._remote_functions = []
        self._tcpSerSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcpSerSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._tcpSerSock.bind((self._hostname, self._port))
        self._tcpSerSock.listen(50)
        self._ready = True

    def _register_function(self, func, name):
        self._remote_functions.append(func)

    def __del__(self):
        self._tcpSerSock.close()

    def run(self):
        def function_process(tcp_client_socket):
            input_buffer = None
            total_data_size = 0
            remote_function = None
            while True:
                message = tcp_client_socket.recv(self._buffer_size)
                if not message:
                    break
                if not remote_function:
                    if message[:3] != datalib.MESSAGE_HEADER:
                        raise ReferenceError('Message does not contain header information and a function reference')
                    header, message = message.split('%(delimiter)s%(header_end)s' % dict(
                        delimiter=datalib.HEADER_DELIMITER,
                        header_end=datalib.MESSAGE_HEADER_END))
                    header, function, message_length = header.split(datalib.HEADER_DELIMITER)
                    remote_function = self._remote_functions[int(function)]
                    total_data_size = int(message_length)
                    input_buffer = datalib.InputStreamBuffer(message)
                else:
                    input_buffer.extend(message)
                if total_data_size < input_buffer.size:
                    raise OverflowError(
                        'The size {0} is longer than the expected message size {1}'.format(input_buffer.size,
                                                                                           total_data_size))
                elif total_data_size == input_buffer.size:
                    frame = input_buffer[0:input_buffer.size]
                else:
                    continue
                args, kwargs = datalib.deserialize_data(frame)
                try:
                    return_value = remote_function(*args, **kwargs)
                except Exception as e:
                    return_value = e
                tcp_client_socket.send(datalib.serialize_data(return_value))
                remote_function = None
            tcp_client_socket.close()

        while True:
            tcp_client_socket, _ = self._tcpSerSock.accept()
            p = multiprocessing.Process(target=function_process, args=(tcp_client_socket,))
            p.start()

