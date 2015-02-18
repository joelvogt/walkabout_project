from walkabout.helpers.configlib import ConfigParamters

client_id = 'osx_client'

modules = ConfigParamters(default=dict(
    buffer_size=8192,
    connection='tcpsock',
    serialization=dict(
        data='python_pickling',
        results='python_pickling')))
