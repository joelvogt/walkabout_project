import sys

if '/Users/joelvogt/PyCharmProjects/walkabout_project/' not in sys.path:
    sys.path.append('/Users/joelvogt/PyCharmProjects/walkabout_project/')
from Mgr import *
import numpy as np


def doSum(arr):
    return [np.sum(arr) for i in range(1000)][-1]


class pxObj:
    pass


M = Mgr("/Applications/Pixelman/", 'LX')
M.open()
if M.isRunning():
    print 'Pixelman Manager is running'
else:
    print 'Failed to start Pixelman Manager'
#
##Create a device for the first chip
D = MpxDevice(M.mgr, 0)
print 'Connected to ', D.chipId()

nItr = 100
acqTime = 0.001

import time

startRem = time.time()
from walkabout.base.client import *

server = import_module('basic_operations', '137.138.79.116')

for i in range(0, nItr):
    D.performFrameAqc(numberOfFrames=1, timeOfEachAcq=acqTime)
    a = D.getFrame16()
    server.b_doSum(a)

print len(list(server.b_doSum))
endRem = time.time()

startLoc = time.time()
for i in range(0, nItr):
    D.performFrameAqc(numberOfFrames=1, timeOfEachAcq=acqTime)
    print i
    # print i, numpy.sum(D.getFrame16())
    a = D.getFrame16()
    doSum(a)

endLoc = time.time()

remotefps = nItr / (endRem - startRem)
localfps = nItr / (endLoc - startLoc)

diffps = 1.0 / remotefps - 1.0 / localfps

print "Remote fps =", round(nItr / (endRem - startRem), 3), " Local fps =", round(nItr / (endLoc - startLoc),
                                                                                  3), " Overhead = ", round(
    1000 * diffps, 3), "ms/frame"




# print server.get_sum(D.getFrame16())


# print server.get_sum(D.getFrame16)



