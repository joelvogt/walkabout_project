# -*- coding: utf-8 -*-
"""
	Created on Wed Feb 20 14:54:08 2013
	
	@author: erikfrojdh
	
	Script to help automate the measurements at the syncrothron in Bern
	"""

from Mgr import *

##Create a Pixelman Manager Object and initialize
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

		
