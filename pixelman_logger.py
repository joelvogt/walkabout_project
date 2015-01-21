# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
from helpers.moduleslib import networked_function

events = 0
@networked_function(buffered=True)
def write(event):
    global events
    events += 1
    print(events)