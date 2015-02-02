# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import importlib

from cernthon.serialization import SerializationEndpoint


class ModuleConfig(object):
    @staticmethod
    def get_python_object(component_type, implementation, module=None):
        module = '.%s' % module if module else ''
        return '%s.%s.%s%s' % ('cernthon', component_type, implementation, module)


    def __init__(self, hostname, port):
        self._hostname = hostname
        self._port = port


    def server_factory(self, config):
        connection_module = importlib.import_module(
            ModuleConfig.get_python_object('connection', config.pop('connection'), 'server'))
        serialization = config.pop('serialization')
        receive_data_func = importlib.import_module(
            ModuleConfig.get_python_object('serialization', serialization['data'])).deserialize
        return_results_func = importlib.import_module(
            ModuleConfig.get_python_object('serialization', serialization['results'])).serialize
        s_endpoint = SerializationEndpoint(send_func=return_results_func, receive_func=receive_data_func)
        config['hostname'] = self._hostname
        config['endpoint'] = s_endpoint
        self._port += 1
        config['port'] = self._port
        return connection_module.Server(**config)

    @staticmethod
    def client_configuration(server):
        return dict(server_socket=(server._hostname, server._port),
                    buffer_size=server._buffer_size,
                    unbuffered_methods=server._unbuffered_methods,
                    buffered_methods=server._buffered_methods)
