# -*-coding:utf-8 *-
__author__ = u'Joël Vogt'
import xmlrpclib
import imp
from collections import namedtuple
import os
import sys
import time

from walkabout.serialization import SerializationEndpoint


config_file = os.path.join(os.curdir, 'config.py')

if os.path.exists(config_file):
    cernthon_config = imp.load_source('config', config_file)
else:
    CernthonConfig = namedtuple('CernthonConfig', ['client_id', 'modules'])
    client_id = '%s-%f' % (sys.platform, time.time())
    modules = dict(
        remote_file=dict(
            buffer_size=8192,
            connection='tcpsock',
            serialization=dict(
                data='python_pickling',
                results='python_pickling'
            )
        )
    )
    cernthon_config = CernthonConfig(client_id, modules)
    # raise AttributeError("config.py not found, the system can't be configured")


def import_module(module_name, directory_service_hostname='127.0.0.1', port=9000):
    """
    Instantiates a remote module on the walkabout_project server and returns a proxy object with the interface of that module.
    :param module_name: The name of the remote module that the user wants to import
    :param directory_service_hostname: The hostname or IP of the walkabout_project server where the modules are hosted
    :param port: The port number of the walkabout_project directory serice
    :return: A Client object if the module is found, otherwise an ImportError error
    """
    modules_directory_service = xmlrpclib.ServerProxy(
        'http://%s:%d' %
        (
            directory_service_hostname,
            port),
        allow_none=True)
    config = modules_directory_service.import_module(module_name,
                                                     cernthon_config.client_id,
                                                     cernthon_config.modules)

    client_module = __import__(config['connection_module_url'], fromlist=[''])
    data_module = __import__(config['data_module_url'], fromlist=[''])
    results_module = __import__(config['results_module_url'], fromlist=[''])
    send_data_func = data_module.serialize
    receive_results_func = results_module.deserialize
    return client_module.Client(server_socket=config['server_socket'],
                                buffer_size=config['buffer_size'],
                                unbuffered_methods=config['unbuffered_methods'],
                                buffered_methods=config['buffered_methods'],
                                endpoint=SerializationEndpoint(send_func=send_data_func,
                                                               receive_func=receive_results_func))
