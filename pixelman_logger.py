# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
from helpers.moduleslib import networked_function
from helpers.datalib import InputStreamBuffer

logfile=None
@networked_function(buffered=True)
def write(event):
    global logfile
    if not logfile:
        print 'log'
        logfile = InputStreamBuffer(file_name='out.txt')
    logfile.extend(event)
