# -*- coding: utf-8 -*-
"""
Created on Mon Jun 07 16:41:05 2010

@author: ltlustos
"""
import ctypes
from time import strftime, localtime

import numpy as np

from PmMgrApi import PmMgrApi
from PmMgrApi import PmMgrApiConst
import matplotlib.pyplot as plt


plt.ion()

import os
import time


def linreg(X, Y):
    """
    from: Greg Pinero, http://www.answermysearches.com/how-to-do-a-simple-linear-regression-in-python/124/
    Summary
        Linear regression of y = ax + b
    Usage
        real, real, real = linreg(list, list)
    Returns coefficients to the regression line "y=ax+b" from x[] and y[], and R^2 Value
    """
    if len(X) != len(Y):  raise ValueError, 'unequal length'
    N = len(X)
    Sx = Sy = Sxx = Syy = Sxy = 0.0
    for x, y in map(None, X, Y):
        Sx = Sx + x
        Sy = Sy + y
        Sxx = Sxx + x * x
        Syy = Syy + y * y
        Sxy = Sxy + x * y
    det = Sxx * N - Sx * Sx
    a, b = (Sxy * N - Sy * Sx) / det, (Sxx * Sy - Sx * Sxy) / det
    meanerror = residual = 0.0
    for x, y in map(None, X, Y):
        meanerror = meanerror + (y - Sy / N) ** 2
        residual = residual + (y - a * x - b) ** 2
    RR = 1 - residual / meanerror
    ss = residual / (N - 2)
    Var_a, Var_b = ss * N / det, ss * Sxx / det
    # print "y=ax+b"
    # print "N= %d" % N
    #print "a= %g \\pm t_{%d;\\alpha/2} %g" % (a, N-2, sqrt(Var_a))
    #print "b= %g \\pm t_{%d;\\alpha/2} %g" % (b, N-2, sqrt(Var_b))
    #print "R^2= %g" % RR
    #print "s^2= %g" % ss
    return a, b, RR


class PmError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class MpxDevice(object):
    __mgr__ = None
    ID = None
    info = None
    DACs = None
    __matrixsize__ = None

    def __init__(self, mgr, id):
        self.__mgr__ = mgr
        self.ID = id
        self.info = self.__mgr__.mpxCtrlGetDevInfo(self.ID)
        self.DACs = DAC(self.__mgr__, self.ID)
        self.__matrixsize__ = [self.info.pixCount / 256 / self.info.numberOfRows,
                               self.info.pixCount / 256 / self.info.numberOfRows]

    def chipId(self):
        return self.info.chipboardID

    def reconnect(self):
        self.__mgr__.mpxCtrlReconnectMpx(self.ID)

    def revive(self, ):
        self.__mgr__.mpxCtrlReviveMpxDevice(self.ID)

    # mgr.mpxCtrlGetHwInfoCount(devId)
    def polarity(self, pol=None):
        if pol == None:
            return self.__mgr__.mpxCtrlGetPolarity(self.ID)
        self.__mgr__.mpxCtrlSetPolarity(self.ID, pol)

    def acqMode(self, m=None):
        if m == None:
            return self.__mgr__.mpxCtrlGetAcqMode(self.ID)
        self.__mgr__.mpxCtrlSetAcqMode(self.ID, m)

    def saveCfg(self, filename):
        self.__mgr__.mpxCtrlSaveMpxCfg(self.ID, filename)

    def loadCfg(self, filename):
        self.__mgr__.mpxCtrlLoadMpxCfg(self.ID, filename)

    def savePixelsCfg(self, filename):
        self.__mgr__.mpxCtrlSavePixelsCfg(self.ID, filename)

    def loadPixelsCfg(self, filename):
        self.__mgr__.mpxCtrlLoadPixelsCfg(self.ID, filename)

    def getPixelsCfg(self):
        return self.__mgr__.mpxCtrlGetPixelsCfg(self.ID, self.info.mpxType)

    def setPixelsCfg(self, pixCfg):
        self.__mgr__.mpxCtrlSetPixelsCfg(self.ID, pixCfg)

    def setMode(self, mode='MPX'):
        cfg = self.getPixelsCfg()
        if mode == 'Counting':
            cfg['mode'] = 0
        elif mode == 'ToT':
            cfg['mode'] = 1
        elif mode == 'ToA_1hit':
            cfg['mode'] = 2
        elif mode == 'ToA':
            cfg['mode'] = 3
        else:
            raise TypeError('Unknown operation mode use one of: mpx, ToT, ToA_1hit or ToA')

        self.setPixelsCfg(cfg)

    def performFrameAqc(self, numberOfFrames, timeOfEachAcq, filename=None, format='i16', binary=False, sparsexy=False,
                        append=False):
        format = format.upper()
        if format == 'I16':
            format = PmMgrApiConst.FSAVE_I16
        elif format == 'I32':
            format = PmMgrApiConst.FSAVE_I32
        elif format == 'DOUBLE':
            format = PmMgrApiConst.FSAVE_DOUBLE
        else:
            raise NameError(format + 'is not vaild [I16, I32 or DOUBLE]')
        if filename != None:
            fileFlags = format
            if binary:
                fileFlags = fileFlags | PmMgrApiConst.FSAVE_BINARY
            else:
                fileFlags = fileFlags | PmMgrApiConst.FSAVE_ASCII
            if sparsexy:
                fileFlags = fileFlags | PmMgrApiConst.FSAVE_SPARSEXY
            if append:
                fileFlags = fileFlags | PmMgrApiConst.FSAVE_APPEND
        else:
            fileFlags = 0
        self.__mgr__.mpxCtrlPerformFrameAcq(self.ID, numberOfFrames, timeOfEachAcq, fileFlags, filename)

    def performTestPulseAcq(self, spacing=2, pulseHeight=0.5, period=0.0001, pulseCount=1000, manual=None,
                            manualTPBits=False):
        self.__mgr__.mpxCtrlPerformTestPulseAcq(self.ID, spacing, pulseHeight, period, pulseCount, manual, manualTPBits)

    def saveFrame(self, filename, framenumber=0, format='I16', binary=False, sparsexy=False, append=False):
        format = format.upper()
        if format == 'I16':
            format = PmMgrApiConst.FSAVE_I16
        elif format == 'I32':
            format = PmMgrApiConst.FSAVE_I32
        elif format == 'DOUBLE':
            format = PmMgrApiConst.FSAVE_DOUBLE
        else:
            raise NameError(format + 'is not vaild [I16, I32 or DOUBLE]')
        flags = format
        if binary:
            flags = flags | PmMgrApiConst.FSAVE_BINARY
        else:
            flags = flags | PmMgrApiConst.FSAVE_ASCII
        if sparsexy:
            flags = flags | PmMgrApiConst.FSAVE_SPARSEXY
        if append:
            flags = flags | PmMgrApiConst.FSAVE_APPEND
        self.__mgr__.mpxCtrlSaveFrame(self.ID, filename, framenumber, flags)

    def performDigitalTest(self, show=True, delay=0.0):
        self.__mgr__.mpxCtrlPerformDigitalTest(self.ID, show, delay)

    def abortOperation(self):
        self.__mgr__.mpxCtrlAbortOperation(self.ID)

    def setTrigger(self, trigger=PmMgrApiConst.TRIGGER_ACQSTART):
        self.__mgr__.mpxCtrlTrigger(self.ID, trigger)

    def getFrame(self, framenumber=0, format='i16'):
        format = format.upper()
        if format == 'I16':
            return self.getFrame16(framenumber)
        elif format == 'I32':
            return self.getFrame32(framenumber)
        elif format == 'DOUBLE':
            return self.getFrameDouble(framenumber)
        else:
            raise NameError(format + 'is not vaild [I16, I32 or DOUBLE]')

    def getFrame16(self, framenumber=0):
        return np.flipud(self.__mgr__.mpxCtrlGetFrame16(self.ID, self.__matrixsize__, framenumber))

    def getFrame32(self, framenumber=0):
        return np.flipud(self.__mgr__.mpxCtrlGetFrame32(self.ID, self.__matrixsize__, framenumber))

    def getFrameDouble(self, framenumber=0):
        return np.flipud(self.__mgr__.mpxCtrlGetFrameDouble(self.ID, self.__matrixsize__, framenumber))

    def scanDac(self, dac, start, stop, step=1, tacq=1, nacq=1, filename=None, format='i16', binary=False,
                sparsexy=False, append=False, tp=False, pulseHeigh=0.2, pulseCount=100):
        """ Function to scan one dac and save the frames"""

        # Check the range of the scan
        maxdac = self.DACs.max(dac)
        if start < 0:
            raise PmError('invalid DAC start value %d for ' % start + dac)
        if stop > maxdac:
            raise PmError('invalid DAC stop value %d for ' % stop + dac)
        if filename != None:
            (dirname, filename) = os.path.split(filename)
            (filename, ext) = os.path.splitext(filename)

        #Genereate steps and save the previous value
        dacs = np.arange(start, stop, step)
        meancount = np.zeros(dacs.shape) * np.nan
        dacbkp = self.DACs[dac]

        #        if saveLog==True:
        #            #Check if file exists and raise error if we have set overWrite to false
        #            if os.path.isfile(os.path.join(dirname, filename)+'_log.txt') and overWrite==False:
        #                raise IOError('File already exists set overWrite=True or use a different filename')
        #            try:
        #                log=open(os.path.join(dirname, filename)+'_log.txt', 'w')
        #            except IOError:
        #                os.makedirs(path)
        #                log=open(os.path.join(dirname, filename)+'_log.txt', 'w')

        for i in np.arange(dacs.size):
            self.DACs[dac] = dacs[i]
            if tp:
                self.performTestPulseAcq(pulseHeight=pulseHeigh, pulseCount=pulseCount)
            else:
                self.performFrameAqc(nacq, tacq)
            if filename != None:
                if append == False:
                    self.saveFrame(dirname + '/' + filename + '_' + dac + '%i_' % dacs[i] + '%4i' % 0 + ext, 0, format,
                                   binary, sparsexy, append)
                elif append == True:
                    self.saveFrame(dirname + '/' + filename + ext, 0, format, binary, sparsexy, append)
            data = self.getFrame(format=format)
            for j in np.arange(1, nacq):
                if filename != None:
                    self.saveFrame(dirname + '/' + filename + '_' + dac + '%i_' % dacs[i] + '%4i' % j + ext, 0, format,
                                   binary, sparsexy, append)
                data = data + self.getFrame(format=format)

            meancount[i] = np.mean(data[0:10, 0:10])
            time.sleep(0.01)
            print('%d ' % dacs[i]),  #force plot update
        self.DACs[dac] = dacbkp
        plt.figure()
        plt.plot(dacs, meancount)
        return dacs, meancount

    def thlScan(self, dac, start, stop,
                step=1,
                tacq=1,
                nacq=1,
                filename=None,
                format='i16',
                binary=False,
                sparsexy=False,
                append=False,
                useTestPulses=False,
                saveLog=False,
                overWrite=False,
                pulseHeight=0.2,
                pulseCount=100,
                spacing=2):
        """ Function to scan thl dac and save the frames"""

        # Check the range of the scan
        maxdac = self.DACs.max(dac)
        if start < 0:
            raise PmError('invalid DAC start value %d for ' % start + dac)
        if stop > maxdac:
            raise PmError('invalid DAC stop value %d for ' % stop + dac)
        if filename != None:
            (dirname, filename) = os.path.split(filename)
            (filename, ext) = os.path.splitext(filename)

        #Genereate steps and save the previous value
        dacs = np.arange(start, stop, step)
        meancount = np.zeros(dacs.shape) * np.nan
        dacbkp = self.DACs[dac]

        if saveLog == True:
            #Check if file exists and raise error if we have set overWrite to false
            if os.path.isfile(os.path.join(dirname, filename) + '_log.txt') and overWrite == False:
                raise IOError('File already exists set overWrite=True or use a different filename')
            try:
                log = open(os.path.join(dirname, filename) + '_log.txt', 'w')
            except IOError:
                os.makedirs(path)
                log = open(os.path.join(dirname, filename) + '_log.txt', 'w')

        #List with values to write to the log
        thlCodeList = []
        thlAnalogList = []
        fbkAnalogList = []
        frameSumList = []

        #SCAN
        for i in np.arange(dacs.size):
            #Set DAC
            self.DACs[dac] = dacs[i]

            if useTestPulses:
                self.performTestPulseAcq(pulseHeight=pulseHeight, pulseCount=pulseCount, spacing=spacing)
            else:
                self.performFrameAqc(nacq, tacq)
            if filename != None:
                if append == False:
                    self.saveFrame(dirname + '/' + filename + '_' + dac + '%i_' % dacs[i] + '%4i' % 0 + ext, 0, format,
                                   binary, sparsexy, append)
                elif append == True:
                    if i == 0:
                        self.saveFrame(dirname + '/' + filename + ext, 0, format, binary, sparsexy, False)
                    else:
                        self.saveFrame(dirname + '/' + filename + ext, 0, format, binary, sparsexy, append)

            data = self.getFrame(format=format)

            #            for j in np.arange(1, nacq):
            #                if filename!=None:
            #                    self.saveFrame(dirname+'/'+filename+'_'+ dac+'%i_' %dacs[i] +'%4i' %j + ext, 0, format, binary, sparsexy, append)
            #                data = data + self.getFrame(format=format)

            meancount[i] = np.mean(data)

            time.sleep(0.1)

            #Measure THL and FBK
            thl = self.DACs.analog('THL', senseCount=3)
            fbk = self.DACs.analog('FBK', senseCount=3)

            thlCodeList.append(dacs[i])
            thlAnalogList.append(thl)
            fbkAnalogList.append(fbk)
            frameSumList.append(data.sum())

            print('%d ' % dacs[i]),  #force plot update
        self.DACs[dac] = dacbkp

        #plt.figure()
        #plt.plot(dacs, meancount)

        a, b, c = linreg(thlCodeList, thlAnalogList)
        fbk_m = sum(fbkAnalogList) / len(fbkAnalogList)

        if saveLog == True:
            log.write('Scan Log for ' + self.info.chipboardID + '\n')
            if self.info.mpxType == 1:
                log.write('Chip type: Medipix2\n')
            elif self.info.mpxType == 2:
                log.write('Chip type: Medipix2MXR\n')
            elif self.info.mpxType == 3:
                log.write('Chip type: Timepix\n')
            elif self.info.mpxType == 4:
                log.write('Chip type: Medipix3\n')
            else:
                log.write('Chip type: Unknown\n')
            log.write('Time: ' + strftime("%a, %d %b %Y %H:%M:%S", localtime()) + '\n')
            log.write('THL Fit: ' + str(a) + '*x+' + str(b) + '\n')
            log.write('FBK Mean: ' + str(fbk_m) + '\n')
            log.write(
                'THL'.ljust(8) + 'THL (Analog)'.ljust(15) + 'FBK (Analog)'.ljust(15) + 'THL-FBK'.ljust(15) + 'Sum\n')
            for i in range(len(thlCodeList)):
                th = a * thlCodeList[i] + b - fbk_m
                field_width = 10
                thl_s = "%5.*f" % (field_width, thlAnalogList[i])
                fbk_s = "%5.*f" % (field_width, fbkAnalogList[i])
                eff_s = "%5.*f" % (field_width, th)
                frame_s = "%5.*i" % (field_width, frameSumList[i])
                log.write(
                    str(thlCodeList[i]).ljust(8) + thl_s.ljust(15) + fbk_s.ljust(15) + eff_s.ljust(15) + frame_s.ljust(
                        15) + '\n')
            log.close()
        return dacs, meancount


class Mgr(object):
    mgr = None
    devices = dict()

    def __init__(self, rootpath='/Applications/Pixelman', system='LX'):
        self.mgr = PmMgrApi(rootpath, system)
        self.__class__.mgr = self.mgr

    def __del__(self):
        if not (self.mgr == None):
            if self.mgr.mgrIsRunning():
                self.mgr.mgrExitManager()
            self.mgr = None
        self.__class__.mgr = self.mgr

    def open(self, flags=3):
        self.mgr.mgrInitManager()
        devId, N = self.mgr.mpxCtrlGetFirstMpx()
        self.devices.clear()
        self.devices[devId] = MpxDevice(self.mgr, devId)
        for i in np.arange(N - 1):
            devId = self.__mgr__.mpxCtrlGetNextMpx(devId)
            self.devices[devId] = MpxDevice(self.mgr, devId)

    def close(self):
        self.mgr.mgrExitManager()

    def isRunning(self):
        return self.mgr.mgrIsRunning()

    def findNewDevices(self):
        self.mgr.mpxCtrlFindNewMpxs()
        devId, N = self.mgr.mpxCtrlGetFirstMpx()
        if N > self.devices.count:
            if not (self.devices.has_key(devId)):
                self.devices[devId] = MpxDevice(self.mgr, devId)
                for i in np.arange(N - 1):
                    devId = self.mgr.mpxCtrlGetNextMpx(devId)
                    if not (self.devices.has_key(devId)):
                        self.devices[devId] = MpxDevice(self.mgr, devId)


class DAC(object):
    __mgr__ = None
    __dacs__ = None
    __def__ = None
    __devid__ = None
    __chipnumber__ = None

    def __init__(self, mgr, devid, chipNumber=0, matrixsize=[256, 256]):
        self.__mgr__ = mgr
        self.__devid__ = devid
        self.__chipnumber__ = chipNumber
        self.__def__ = self.__mgr__.mpxCtrlGetDACsNames(self.__devid__)
        dacVals = self.__mgr__.mpxCtrlGetDACs(self.__devid__, self.__def__.count, self.__chipnumber__)
        keys = self.__def__.dacnames()
        self.__dacs__ = np.ndarray([self.__def__.count], ctypes.c_ushort)
        for i in np.arange(self.__def__.count):
            idx = self.__def__.order[keys[i]]
            self.__dacs__[idx] = dacVals[idx]

    def __getitem__(self, key):
        key = self.__check_valid_key__(key)
        return self.__dacs__[self.__def__.order[key]]

    def __setitem__(self, key, value):
        key = self.__check_valid_key__(key)
        if (value < 0) | (value > self.__def__.max[key.upper()]):
            raise PmError('invaid Dac value')
        self.__dacs__[self.__def__.order[key]] = value
        self.__mgr__.mpxCtrlSetDACs(self.__devid__, self.__dacs__, self.__def__.count, self.__chipnumber__)

        return

    def __check_valid_key__(self, key):
        key = key.upper()
        if not (self.__def__.order.has_key(key)):
            raise PmError('invaid Dac name')
        return key

    def analog(self, key, senseCount=3):
        key = self.__check_valid_key__(key)
        return self.__mgr__.mpxCtrlGetSingleDACAnalog(self.__devid__, 1, self.__def__.order[key], self.__chipnumber__,
                                                      senseCount)

    def getall(self):
        return self.__mgr__.mpxCtrlGetDACsAnalog(self.__devid__, 14)

    def max(self, key):
        dac = self.__check_valid_key__(key)
        return self.__def__.max[key.upper()]


    def scan(self, dac, step=1):
        dac = self.__check_valid_key__(dac)
        maxdac = self.max(dac)
        dacs = np.arange(0, maxdac, step)
        dacbackup = self.__getitem__(dac)  # Save dac
        analogue = np.zeros(dacs.shape)
        for i in np.arange(dacs.size):
            self.__setitem__(dac, dacs[i])
            analogue[i] = self.analog(dac)
        self.__setitem__(dac, dacbackup)  # Restore dac
        return (dacs, analogue)
