# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import importlib

from cernthon.serialization import SerializationEndpoint


class ModuleConfig(object):
    @staticmethod
    def get_class(component_type, implementation, module=None):
        module = '.%s' % module if module else ''
        return importlib.import_module('%s.%s.%s%s' % ('cernthon', component_type, implementation, module))

    def __init__(self, hostname, port):
        self._hostname = hostname
        self._port = port


    def server_factory(self, config):
        connection_module = ModuleConfig.get_class('connection', config.pop('connection'), 'server')
        serialization = config.pop('serialization')
        receive_data_func = ModuleConfig.get_class('serialization', serialization['data']).deserialize
        return_results_func = ModuleConfig.get_class('serialization', serialization['results']).serialize
        s_endpoint = SerializationEndpoint(send_func=return_results_func, receive_func=receive_data_func)
        config['hostname'] = self._hostname
        config['endpoint'] = s_endpoint
        self._port += 1
        config['port'] = self._port
        return connection_module.Server(**config)

    def client_configuration(self, server):
        return server._hostname, \
               server._port, \
               server._buffer_size, \
               dict(
                   unbuffered_methods=server._unbuffered_methods,
                   buffered_methods=server._buffered_methods)