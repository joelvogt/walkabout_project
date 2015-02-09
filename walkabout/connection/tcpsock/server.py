# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import socket
import multiprocessing

from walkabout.connection import CLOSE_CONNECTION
from walkabout.connection.tcpsock import HEADER_DELIMITER, MESSAGE_HEADER_END, MESSAGE_HEADER
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
    while is_used_by_client:
        while is_used_by_client:
            message = tcp_client_socket.recv(buffer_size)
            if CLOSE_CONNECTION == message:
                break

            if not message:
                is_used_by_client = False
                return_value = -1
                break

            if not remote_function:
                if message[:3] != MESSAGE_HEADER:
                    return_value = ReferenceError(
                        'Message does not contain header information and a function reference')
                    frame = None
                    break

                header, message = message.split('%(delimiter)s%(header_end)s' % dict(
                    delimiter=HEADER_DELIMITER,
                    header_end=MESSAGE_HEADER_END))
                header, function, message_length = header.split(HEADER_DELIMITER)
                try:
                    remote_function = remote_functions[int(function)]
                    total_data_size = int(message_length)
                    input_buffer = InputStreamBuffer(data=message, buffer_size=buffer_size)
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
            print('debug 0')
            t = endpoint.to_receive(frame)
            print('debug 1')
            try:
                if len(t) == 2:
                    print('debug 2')
                    args, kwargs = t  # endpoint.to_receive(frame)
                    print('debug 2.1')
                    return_value = remote_function(*args, **kwargs)
                    print('debug 2.2')
                else:
                    print('debug 3')
                    print(len(t))
                    print(type(t))
                    print(len(list(t)))
                    # remote_function(list(t))
                    print('debug 3.1')
            except Exception as e:
                print('error')
                print(e)
                return_value = e

        if return_value != -1:
            tcp_client_socket.send(endpoint.to_send(return_value))
            remote_function = None

    tcp_client_socket.close()


class Server(object):
    def __init__(self, hostname, port, buffer_size, endpoint):
        self.hostname = hostname
        self.port = port
        self.buffer_size = buffer_size
        self.buffered_methods = []
        self.unbuffered_methods = []
        self._endpoint = endpoint
        self._remote_functions = []
        self._tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._tcp_server_socket.bind((self.hostname, self.port))
        self._tcp_server_socket.listen(5)
        self._ready = True

    def _register_function(self, func, name):
        self._remote_functions.append(func)

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

    def __call__(self, buffered_func, buffered=False):
        def buffered_function(func):
            def on_call(params):
                return [func(*args, **kwargs) for args, kwargs in params]

            return on_call

        networked_func = buffered_func
        if buffered:
            self.buffered_methods.append(buffered_func.__name__)
            networked_func = buffered_function(networked_func)
        else:
            self.unbuffered_methods.append(buffered_func.__name__)
        self._register_function(networked_func, name=buffered_func.__name__)