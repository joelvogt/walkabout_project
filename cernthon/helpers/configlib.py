# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import importlib


class ModuleConfig(object):

    @staticmethod
    def get_class(component_type, implementation, module):
        return importlib.import_module('%s.%s.%s.%s' % ('cernthon', component_type, implementation, module))

    def __init__(self, hostname, port):
        self._hostname = hostname
        self._port = port

    def server_factory(self, config):
        connection_module = ModuleConfig.get_class('connection', config.pop('connection'),'server')
        config['hostname'] = self._hostname
        self._port += 1
        config['port'] = self._port
        return connection_module.Server(**config)
