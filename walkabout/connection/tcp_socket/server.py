# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import socket
from multiprocessing.dummy import Process, current_process

from walkabout.connection import CLOSE_CONNECTION, FLUSH_BUFFER_REQUEST
from walkabout.connection.tcp_socket import MESSAGE_HEADER, HEADER_DELIMITER, MESSAGE_HEADER_END, \
    get_header_from_message
from walkabout.helpers.datalib import InputStreamBuffer

















# from pathos.multiprocessing import ProcessingPool as Pool
# from pathos.helpers import cpu_count

TIMEOUT = 10
STATE_RUNNING = 0
STATE_FINISHING = 1
STATE_END_CALL = 2


def _function_process(tcp_client_socket, buffer_size, remote_functions, endpoint):
    input_buffer = None
    total_data_size = 0
    remote_function = None
    """ return_value == -1 if no function_ref was called.
    None can be returned by functions without explicit return value"""
    function_ref = None
    frame = None
    next_frame = None
    message = None
    event = None
    state = STATE_RUNNING
    return_value = -1
    is_used_by_client = True

    # Locally stored references of commonly used functions and data objects
    f_input_buffer_extend = None

    f_str_join = ''.join

    f_tcp_socket_receive = tcp_client_socket.recv
    f_tcp_socket_send = tcp_client_socket.send

    f_endpoint_to_send = endpoint.to_send
    f_endpoint_to_receive = endpoint.to_receive

    while is_used_by_client:
        while is_used_by_client:
            if state == STATE_RUNNING:
                message = f_tcp_socket_receive(buffer_size)

            elif state == STATE_FINISHING:

                if next_frame:
                    message = next_frame
                    next_frame = None
                else:

                    state = STATE_END_CALL
                    return_value = -1
                    break

            if CLOSE_CONNECTION == message:
                is_used_by_client = False
                break

            if FLUSH_BUFFER_REQUEST == message[-3:]:

                event = FLUSH_BUFFER_REQUEST
                state = STATE_FINISHING

                if len(message) > 3:
                    message = message[:-3]
                else:
                    continue
            if not message:
                is_used_by_client = False
                return_value = -1
                break

            if not remote_function:
                if next_frame:
                    message = f_str_join([next_frame, message])
                    next_frame = None
                if message[:3] != MESSAGE_HEADER:
                    return_value = ReferenceError(
                        'Message does not contain header information and a function_ref reference')
                    frame = None
                    break
                try:
                    function_ref, total_data_size, message = get_header_from_message(message)
                    remote_function = remote_functions[function_ref]
                    input_buffer = InputStreamBuffer(buffer_size=buffer_size)
                    f_input_buffer_extend = input_buffer.extend

                except IndexError:
                    return_value = AttributeError("Server side exception: \
                    Remote module doesn't have the function_ref you tried to call")
                    frame = None
                    break

            diff = total_data_size - (input_buffer.size + len(message))
            if diff < 0:
                next_frame = message[diff:]
                message = message[:diff]
            f_input_buffer_extend(message)

            if total_data_size < input_buffer.size:
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
        f_input_buffer_extend = None
        if frame:
            args, kwargs = f_endpoint_to_receive(frame)
            frame = None
            try:
                return_value = remote_function(*args, **kwargs)
            except Exception as e:
                e.message = "server exception {0}".format(e.message)
                return_value = e

        if return_value != -1:
            if isinstance(return_value, Exception):
                is_used_by_client = False

            serialized_content = f_endpoint_to_send(return_value)
            return_message = '%(header)s' \
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
            f_tcp_socket_send(return_message)
            remote_function = None
            return_value = -1
        if state == STATE_END_CALL:
            if event:
                f_tcp_socket_send(event)
                event = None
                state = STATE_RUNNING
    f_tcp_socket_send(CLOSE_CONNECTION)
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


    def run(self):
        while current_process().is_alive():
            tcp_client_socket, _ = self._tcp_server_socket.accept()
            p = Process(
                target=_function_process,
                args=(tcp_client_socket,
                      self.buffer_size,
                      self._remote_functions,
                      self._endpoint))
            p.start()
        self._tcp_server_socket.close()

    def __call__(self, networked_func, buffered):
        function_name = networked_func.__name__

        def buffered_function(func):
            # if func.func_code.co_argcount == 1 and cpu_count() > 1:
            #     def on_call(params):
            #         single_arguments = map(lambda x: x[0][0], params)
            #         pool = Pool(processes=cpu_count())
            #         return pool.map(func, single_arguments)
            # else:
            def on_call(params):
                return [func(*args, **kwargs) for args, kwargs in params]

            return on_call

        if buffered:
            self.buffered_methods.append(function_name)
            self._register_function(buffered_function(networked_func), name=function_name)
        else:
            self.unbuffered_methods.append(function_name)
            self._register_function(networked_func, name=function_name)
