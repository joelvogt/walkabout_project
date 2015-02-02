# -*- coding:utf-8 -*-
from cernthon.helpers.configlib import ModuleConfig

__author__ = u'Joël Vogt'
import imp
from SimpleXMLRPCServer import SimpleXMLRPCServer
import socket
import pprint
from multiprocessing import Process
import os


class ModulesDirectoryService(object):
    def __init__(self, hostname='localhost', port=9000, modules=None):
        if not modules:
            modules = {}
        self._next_port = port
        self._do_run = True
        self._connection_config = ModuleConfig(hostname, port)
        self._modules = modules
        self._server = SimpleXMLRPCServer((hostname, port))  # , allow_none=True)

        self._modules_processes = {}
        try:
            self._hostname = socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            self._hostname = hostname
        self._server.register_instance(self)

    def bind_module(self, modules_process, module_binder_instance, module_ref):
        module = imp.load_source(module_ref['name'], module_ref['file'])
        map(lambda x: module_binder_instance(*x), module.networked_function.functions_registry)
        module.networked_function.functions_registry = []
        module_binder_process = Process(target=module_binder_instance.run, name=module_ref['name'])
        modules_process[module_ref['name']] = [module_binder_process,
                                               module_binder_instance.connection_information(),
                                               os.path.getmtime(self._modules[module_ref['name']]['file'])]
        module_binder_process.start()

    def import_module(self, module_name, client_id, config):


        if client_id not in self._modules_processes:
            self._modules_processes[client_id] = {}
        if module_name not in self._modules:
            raise ImportError('Cannot find %s' % module_name)
        if module_name not in self._modules_processes[client_id]:
            module_binder_instance = self._connection_config.server_factory(config[module_name])
            self.bind_module(self._modules_processes[client_id], module_binder_instance, self._modules[module_name])
        elif os.path.getmtime(self._modules[module_name]['file']) > self._modules_processes[client_id][module_name][
            2]:
            self._modules_processes[client_id][module_name][0].terminate()
            self._modules_processes[client_id][module_name][0].join()
            del self._modules_processes[client_id][module_name]
            module_binder_instance = self._connection_config.server_factory(config[module_name])
            self.bind_module(self._modules_processes[client_id], module_binder_instance, self._modules[module_name])
        return self._modules_processes[client_id][module_name][1]

    def on_start(self):
        pprint.pprint('Modules Directory Service {0}:{1}'.format(self._hostname, self._next_port))
        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            self._do_run = False
