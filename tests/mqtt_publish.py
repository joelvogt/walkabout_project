# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'

from clients.walkabout_experiment import ExperimentProducer

fd = open('/Volumes/walkabout/milanodata.txt')
w = ExperimentProducer('pixelman_data', 60)
for frame in fd.readlines():
    w.add_frame(frame)
w.close()