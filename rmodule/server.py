# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import socket
import multiprocessing

from adapters import numpy_adapters as npa, base
from helpers import datamgmt


class Remote_Module_Binder(object):
    def __init__(self, hostname, port, buffer_size=None, adapters=[npa.numpy_to_xmlrpc]):
        self._adapters = adapters
        self._buffered_methods = []
        self._unbuffered_methods = []
        self._hostname = hostname
        self._port = port
        self._buffer_size = buffer_size

    def connection_information(self):
        return self._hostname,\
               self._port,\
               self._buffer_size,\
               dict(
                unbuffered_methods=self._unbuffered_methods,
                buffered_methods=self._buffered_methods
               )

    def _register_function(self, func, name):
        raise NotImplementedError

    def __call__(self, func, buffered=False):
        def buffered_function(func):
            def onCall(params):
                return [func(*args, **kwargs) for args, kwargs in params]
            return onCall
        networked_func = func
        for adapter in self._adapters:
            networked_func = base.function_adapter_mapper(networked_func, adapter)
        if buffered:
            self._buffered_methods.append(func.__name__)
            networked_func = buffered_function(networked_func)
        else:
            self._unbuffered_methods.append(func.__name__)
        self._register_function(networked_func, name=func.__name__)

    def reset(self):
        self._unbuffered_methods = []
        self._buffered_methods = []


class Socket_Module_Binder(Remote_Module_Binder):

    def __init__(self, hostname, port, buffer_size=datamgmt.DEFAULT_BUFFER_SIZE, adapters=[npa.numpy_to_xmlrpc]):
        Remote_Module_Binder.__init__(self, hostname, port, buffer_size, adapters=adapters)
        self._remote_functions = []
        self._tcpSerSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcpSerSock.bind((self._hostname, self._port))
        self._tcpSerSock.listen(5)
        self._ready = True

    def reset(self):
        Remote_Module_Binder.reset()
        self._remote_functions = []

    def _register_function(self, func, name):
        self._remote_functions.append(func)

    def __del__(self):
        self._tcpSerSock.close()

    def run(self):
        def function_process(tcp_client_socket):
            inputbuffer = None
            total_data_size = 0
            remote_function = None
            while True:
                datagram = tcp_client_socket.recv(self._buffer_size)
                if not datagram:
                    break
                if not remote_function:
                    if datagram[:3] != datamgmt.MESSAGE_HEADER:
                        raise ReferenceError('Message does not contain header information and a function reference')
                    header, function, message_length, message = datagram.split(datamgmt.HEADER_DELIMITER)
                    remote_function = self._remote_functions[int(function)]
                    total_data_size = int(message_length)
                    inputbuffer = datamgmt.InputStreamBuffer(message)
                else:
                    inputbuffer.extend(datagram)
                if total_data_size < inputbuffer._size:
                    raise OverflowError('The size {0} is longer than the expected message size {1}'.format(inputbuffer._size, total_data_size))
                elif total_data_size == inputbuffer._size:
                    frame = inputbuffer[0:inputbuffer._size]
                else:
                    continue
                args, kwargs = datamgmt.deserialize_data(frame)
                try:
                    return_value = remote_function(*args, **kwargs)
                except Exception as e:
                    return_value = e
                tcp_client_socket.send(datamgmt.serialize_data(return_value))
                remote_function = None
            tcp_client_socket.close()

        while True:
            tcpCliSock, addr = self._tcpSerSock.accept()
            multiprocessing.Process(target=function_process,args=(tcpCliSock,)).start()

