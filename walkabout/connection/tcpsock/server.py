# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import socket
import multiprocessing
import re

from walkabout.connection import CLOSE_CONNECTION, FLUSH_BUFFER_REQUEST
from walkabout.connection.tcpsock import MESSAGE_HEADER
from walkabout.helpers.datalib import InputStreamBuffer


TIMEOUT = 10


def _function_process(tcp_client_socket, buffer_size, remote_functions, endpoint):
    input_buffer = None
    total_data_size = 0
    remote_function = None
    """ return_value == -1 if no function was called.
    None can be returned by functions without explicit return value"""
    return_value = -1
    frame = None
    is_used_by_client = True
    next_frame = None
    pattern = re.compile('^HDR\|(\S+?)\|(\d+?)\|EOH(.*)', re.DOTALL)

    event = None
    while is_used_by_client:
        while is_used_by_client:
            message = tcp_client_socket.recv(buffer_size)
            if CLOSE_CONNECTION == message:
                is_used_by_client = False
                break

            if FLUSH_BUFFER_REQUEST == message:
                return_value = -1
                if next_frame:
                    print('next frame')
                if frame:
                    print('frame')
                print('end of bufer')
                event = FLUSH_BUFFER_REQUEST
                break
            if not message:
                is_used_by_client = False
                return_value = -1
                break

            if not remote_function:
                if next_frame:
                    message = ''.join([next_frame, message])
                    next_frame = None
                if message[:3] != MESSAGE_HEADER:
                    return_value = ReferenceError(
                        'Message does not contain header information and a function reference')
                    frame = None
                    break
                function, message_length, message = re.match(pattern, message).groups()
                try:
                    remote_function = remote_functions[function]
                    total_data_size = int(message_length)
                    input_buffer = InputStreamBuffer(buffer_size=buffer_size)
                except IndexError:
                    return_value = AttributeError("Server side exception: \
                    Remote module doesn't have the function you tried to call")
                    frame = None
                    break

            diff = total_data_size - (input_buffer.size + len(message))
            if diff < 0:
                next_frame = message[diff:]
                message = message[:diff]
            input_buffer.extend(message)

            if total_data_size < input_buffer.size:
                input_buffer._fd.seek(0)
                frame = None
                return_value = OverflowError(
                    'Server side exception: \
                    The size {0} is longer than \
                    the expected message size {1}'.format(
                        input_buffer.size,
                        total_data_size))

            elif total_data_size == input_buffer.size:
                frame = input_buffer[0:input_buffer.size]
            else:
                continue
            break
        input_buffer = None
        if frame:
            args, kwargs = endpoint.to_receive(frame)
            frame = None
            try:
                return_value = remote_function(*args, **kwargs)
            except Exception as e:
                e.message = "server exception {0}".format(e.message)
                return_value = e

        if return_value != -1:
            if isinstance(return_value, Exception):
                is_used_by_client = False
            tcp_client_socket.send(endpoint.to_send(return_value))
            remote_function = None
            return_value = -1
        if event:
            tcp_client_socket.send(event)
            event = None
    tcp_client_socket.send(CLOSE_CONNECTION)
    tcp_client_socket.close()


class Server(object):
    def __init__(self, hostname, port, buffer_size, endpoint):
        self.hostname = hostname
        self.port = port
        self.buffer_size = buffer_size
        self.buffered_methods = []
        self.unbuffered_methods = []
        self._endpoint = endpoint
        self._remote_functions = {}
        self._tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._tcp_server_socket.bind((self.hostname, self.port))
        self._tcp_server_socket.listen(5)
        self._ready = True

    def _register_function(self, func, name):
        self._remote_functions[name] = func

    def __del__(self):
        self._tcp_server_socket.close()

    def run(self):
        while True:
            tcp_client_socket, _ = self._tcp_server_socket.accept()
            p = multiprocessing.Process(
                target=_function_process,
                args=(tcp_client_socket,
                      self.buffer_size,
                      self._remote_functions,
                      self._endpoint))
            p.start()

    def __call__(self, networked_func, buffered):
        function_name = networked_func.__name__
        def buffered_function(func):
            def on_call(params):
                return [func(*args, **kwargs) for args, kwargs in params]

            return on_call

        if buffered:
            self.buffered_methods.append(function_name)
            self._register_function(buffered_function(networked_func), name=function_name)
        else:
            self.unbuffered_methods.append(function_name)
            self._register_function(networked_func, name=function_name)
