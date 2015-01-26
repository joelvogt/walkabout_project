#!env/bin/python

import ConfigParser

from cernthon.helpers.datalib import string_to_int
from cernthon.base.server import Modules_Directory_Service


config_options = dict(
    directory_service=lambda s: (s,
                                 dict(
                                     map(
                                         lambda o: (o, string_to_int(config.get(s, o))),
                                         config.options(s)
                                     )
                                 )
    ),
    module=lambda s: (s,
                      dict(
                          map(
                              lambda o: (o, config.get(s, o)),
                              config.options(s)
                          )
                      )
    )
)

if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.read('networkmodulesservice.config')
    params = {}
    for key, value in sorted(
            [
                config_options['module'](section)
                if 'module' == section[:6]
                else config_options[section](section)
                for section in config.sections()
            ],
            key=lambda x: x[0]
    ):
        if ':' in key:
            key, sub_key = key.split(':')
            value = {sub_key: value}
        if key not in params:
            params[key] = value
        else:
            params[key].update(value)
    directory = Modules_Directory_Service(modules=params['module'], **params['directory_service'])
    directory.onStart()