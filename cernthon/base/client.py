# -*-coding:utf-8 *-
__author__ = u'Joël Vogt'
import xmlrpclib
import imp

from cernthon.connection.tcpsock.client import Client
import os
from collections import namedtuple


config_file = os.path.join(os.curdir, 'config.py')

if os.path.exists(config_file):
    cernthon_config = imp.load_source('config', config_file)
else:
    CernthonConfig = namedtuple('CernthonConfig', ['client_id', 'modules'])
    client_id = 'osx_client'
    modules = dict(
        pixelman_logger = dict(
            buffer_size = 4096,
            connection = 'tcpsock',
            serialization = dict(
                data = 'python_pickling',
                results = 'python_pickling'
            )
        )
    )
    cernthon_config = CernthonConfig(client_id, modules)
    # raise AttributeError("config.py not found, the system can't be configured")


def import_module(module_name, directory_service_hostname='127.0.0.1', port=9000):
    """
    Instsantiates a remote module on the CERNthon server and returns a proxy object with the interface of that module.
    :param module_name: The name of the remote module that the user wants to import
    :param directory_service_hostname: The hostname or IP of the CERNthon server where the modules are hosted
    :param port: The port number of the CERNthon directory serice
    :return: A Client object if the module is found, otherwise an ImportError error
    """
    modules_directory_service = xmlrpclib.ServerProxy(
        'http://%s:%d' %
        (
            directory_service_hostname,
            port),
        allow_none=True)
    module_server_hostname, port, buffer_size, methods = \
        modules_directory_service.import_module(
            module_name,
            cernthon_config.client_id,
            cernthon_config.modules
        )
    server = Client(module_server_hostname, port, buffer_size, **methods)
    return server
