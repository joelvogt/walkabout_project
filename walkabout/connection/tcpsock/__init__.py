# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'

import re

MESSAGE_HEADER = 'HDR'
MESSAGE_HEADER_END = 'EOH'
HEADER_DELIMITER = '|'

pattern = re.compile('^HDR\|(\S+?)\|(\d+?)\|EOH(.*)', re.DOTALL)


def get_header_from_message(message):
    global pattern
    function_ref, message_length, message = re.match(pattern, message).groups()
    total_data_size = int(message_length)
    return function_ref, total_data_size, message