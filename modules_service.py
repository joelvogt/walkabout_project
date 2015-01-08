#-*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
from rmodule.server import UDP_Module_Binder



import imp

from SimpleXMLRPCServer import SimpleXMLRPCServer
import threading
import socket
import time
import pprint
import multiprocessing
import rmodule.client


def networked_function(buffered=False):
    def wrapper(func):
        networked_function.functions_registry.append((func, buffered))
        return func
    return wrapper

networked_function.functions_registry = []

MODULES_BINDER_REGISTRY = [
    # XMLRPC_Node,
    UDP_Module_Binder,
    UDP_Module_Binder,
    UDP_Module_Binder
]


class Modules_Directory_Service(threading.Thread):

    def __init__(self, hostname='localhost', port=9000, modules={}):
        threading.Thread.__init__(self)
        self._next_port = port
        self._do_run = True
        self._modules = modules
        self._server = SimpleXMLRPCServer((hostname, port), allow_none=True)
        self._modules_processes = map(lambda x:{}, rmodule.client.CLIENTS)
        try:
            self._hostname = socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            self._hostname = hostname
        self._server.register_instance(self)

    def import_module(self, module_name, client=0):
        if module_name in self._modules:
            if module_name not in self._modules_processes[client]:
                self._next_port += 1
                module_ref = self._modules[module_name]
                module = imp.load_source(module_ref['name'], module_ref['file'])
                module_binder_instance = MODULES_BINDER_REGISTRY[client](self._hostname, self._next_port)
                map(lambda x: module_binder_instance(*x), module.networked_function.functions_registry)
                module.networked_function.functions_registry = []
                module_binder_process = multiprocessing.Process(target=module_binder_instance.run, name=module_name)
                module_binder_process.start()
                self._modules_processes[client][module_name] = [module_binder_process, module_binder_instance.connection_information()]
            return self._modules_processes[client][module_name][1]
        else:
            raise ImportError(module_name)

    def onStart(self):
        pprint.pprint('Modules Directory Service {0}:{1}'.format(self._hostname, self._next_port))
        # self.start()
        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            self._do_run = False


    def run(self):
        while self._do_run:
            # print('>>> Directory Service running. Active modules {0}'.format(len(self._module_instances)))
            for client_type in self._modules_processes:
                filter(lambda proc: not client_type[proc][0].is_alive(), client_type.keys())
            # map(self._module_instances.remove, filter(lambda x: not x.is_alive(), self._module_instances))
            time.sleep(10)