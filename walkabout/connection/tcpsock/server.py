# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import socket
import multiprocessing
import re
from collections import defaultdict
import sys
import types

from walkabout.connection import CLOSE_CONNECTION
from walkabout.connection.tcpsock import MESSAGE_HEADER
from walkabout.helpers.datalib import InputStreamBuffer


TIMEOUT = 10


def _shared_global_decorator(func, shared_globals):
    def on_call(*args, **kwargs):
        function_module = sys.modules[func.__module__]
        func_vars = set(filter(lambda x: hasattr(function_module, x), func.__code__.co_names))
        func_globals = set(
            filter(lambda x: type(func.func_globals[x]) not in [types.ModuleType, types.FunctionType, types.MethodType],
                   func.func_globals.keys()))
        used_globals = func_vars.intersection(func_globals)

        for variable in used_globals:
            if variable in shared_globals:
                if func.func_globals[variable] != shared_globals[variable]:
                    func.func_globals[variable] = shared_globals[variable]
            else:
                shared_globals[variable] = None

        result = func(*args, **kwargs)
        for variable in used_globals:
            if func.func_globals[variable] is not shared_globals[variable]:
                shared_globals[variable] = func.func_globals[variable]
        return result

    return on_call


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
    while is_used_by_client:
        while is_used_by_client:
            message = tcp_client_socket.recv(buffer_size)
            if CLOSE_CONNECTION == message:
                is_used_by_client = False
                frame = None
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
            try:
                return_value = remote_function(*args, **kwargs)
            except Exception as e:
                return_value = e

        if return_value != -1:
            if isinstance(return_value, Exception):
                is_used_by_client = False
            tcp_client_socket.send(endpoint.to_send(return_value))
            remote_function = None
            return_value = -1
    tcp_client_socket.send(endpoint.to_send(CLOSE_CONNECTION))
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
        self._shared_globals = defaultdict()

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
        networked_func = _shared_global_decorator(networked_func, self._shared_globals)
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
