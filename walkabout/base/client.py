# -*-coding:utf-8 *-
from walkabout.helpers.configlib import ConfigParameters

__author__ = u'Joël Vogt'
import xmlrpclib
import imp
from collections import namedtuple
import os
import sys

from walkabout.serialization import SerializationEndpoint


config_file = os.path.join(os.curdir, 'config.py')

if os.path.exists(config_file):
    walkabout_config = imp.load_source('config', config_file)
else:
    WalkaboutConfig = namedtuple('WalkaboutConfig', ['client_id', 'modules'])
    client_id = '%s-%d' % (sys.platform, sys.hexversion)
    modules = ConfigParameters(default=dict(
        buffer_size=4096,
        connection='tcp_socket',
        serialization=dict(
            data='python_pickling',
            results='python_pickling')))
    walkabout_config = WalkaboutConfig(client_id, modules)


def import_module(module_name, directory_service_hostname='127.0.0.1', port=9000):
    """
    Instantiates a remote module on the walkabout_project server and
    returns a proxy object with the interface of that module.
    :param module_name: The name of the remote module that the user wants to import
    :param directory_service_hostname: The hostname or IP of the walkabout_project server
    where the modules are hosted
    :param port: The port number of the walkabout_project directory service
    :return: A Client object if the module is found, otherwise an ImportError error
    """

    modules_directory_service = xmlrpclib.ServerProxy(
        'http://%s:%d' %
        (
            directory_service_hostname,
            port),
        allow_none=True)
    config = modules_directory_service.import_module(module_name,
                                                     walkabout_config.client_id,
                                                     walkabout_config.modules)

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
