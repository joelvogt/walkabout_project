# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
from helpers.moduleslib import networked_function

@networked_function(buffered=True)
def write(event):
    print(event)