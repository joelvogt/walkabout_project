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
        self._config_cache = {}


    def server_factory(self, config):
        connection_module = importlib.import_module(
            ModuleConfig.get_python_object('connection', config['connection'], 'server'))
        receive_data_func = importlib.import_module(
            ModuleConfig.get_python_object('serialization', config['serialization']['data'])).deserialize
        return_results_func = importlib.import_module(
            ModuleConfig.get_python_object('serialization', config['serialization']['results'])).serialize
        endpoint = SerializationEndpoint(send_func=return_results_func, receive_func=receive_data_func)
        self._port += 1
        server = connection_module.Server(hostname=self._hostname,
                                          port=self._port,
                                          buffer_size=config['buffer_size'],
                                          endpoint=endpoint)
        self._config_cache[(server._hostname, server._port)] = config
        return server

    def client_configuration(self, server):
        config = self._config_cache[(server._hostname, server._port)]
        return dict(server_socket=(server._hostname, server._port),
                    buffer_size=server._buffer_size,
                    unbuffered_methods=server._unbuffered_methods,
                    buffered_methods=server._buffered_methods,
                    connection_module_url=ModuleConfig.get_python_object('connection', config['connection'], 'client'),
                    data_module_url=ModuleConfig.get_python_object('serialization', config['serialization']['data']),
                    results_module_url=ModuleConfig.get_python_object('serialization',
                                                                      config['serialization']['results']))
