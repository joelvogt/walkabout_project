# -*-coding:utf-8 *-
__author__ = u'Joël Vogt'
import xmlrpclib
import sys

from cernthon.rmodule.client import RemoteModuleProxy


def import_module(module_name, directory_service_hostname='127.0.0.1', port=9000):
    """
    Instsantiates a remote module on the CERNthon server and returns a proxy object with the interface of that module.
    :param module_name: The name of the remote module that the user wants to import
    :param directory_service_hostname: The hostname or IP of the CERNthon server where the modules are hosted
    :param port: The port number of the CERNthon directory serice
    :return: A RemoteModuleProxy object if the module is found, otherwise an ImportError error
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
            sys.subversion[0]
        )
    server = RemoteModuleProxy(module_server_hostname, port, buffer_size, **methods)
    return server
