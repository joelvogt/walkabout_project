# -*- coding: utf-8 -*-
"""
Created on Tue Feb 19 15:25:51 2013

@author: erikfrojdh


Test to import from a .so file

"""

MGRINIT_NOEXHANDLING = 0x10



# -*- coding: utf-8 -*-

import ctypes
from ctypes import *
from os import chdir
import os

import numpy as np


class PmMgrApiConst(object):
    # CONST

    MPX_MAX_CHBID = 64
    MPX_MAX_IFACENAME = 64

    PIXCFG_MASK = 1
    PIXCFG_TEST = 2
    PIXCFG_THL = 3
    PIXCFG_THH = 4
    PIXCFG_MODE = 5
    PIXCFG_GAIN = 6

    TYPE_BOOL = 0  # C bool value (int)
    TYPE_CHAR = 1  # signed char
    TYPE_UCHAR = 2  # unsigned char
    TYPE_BYTE = 3  # byte (unsigned char)
    TYPE_I16 = 4  # signed short
    TYPE_U16 = 5  # unsigned short
    TYPE_I32 = 6  # int
    TYPE_U32 = 7  # unsigned int
    TYPE_FLOAT = 8  # float
    TYPE_DOUBLE = 9  # double
    TYPE_STRING = 10  # zero terminated string
    TYPE_LAST = 11  # border

    FSAVE_BINARY = 0x0001  # save in binary format
    FSAVE_ASCII = 0x0002  # save in ASCII format
    FSAVE_APPEND = 0x0004  # append frame to existing file if exists (multiframe)
    FSAVE_I16 = 0x0010  # save as 16bit integer
    FSAVE_U32 = 0x0020  # save as unsigned 32bit integer
    FSAVE_DOUBLE = 0x0040  # save as double
    FSAVE_NODESCFILE = 0x0100  # do not save description file
    FSAVE_SPARSEXY = 0x1000  # save only nonzero position in [x y count] format
    FSAVE_SPARSEX = 0x2000  # save only nonzero position in [x count] format
    FSAVE_NOFILE = 0x8000  # frame will not be saved :)

    MPX_ORIG = 1  # original medipix2.x
    MPX_MXR = 2  # medipix mxr 2.0
    MPX_TPX = 3  # timepix
    MPX_3 = 4  # medipix 3

    TRIGGER_ACQSTART = 1  # start trigger (mpxCtrlTrigger(TRIGGER_ACQSTART))
    TRIGGER_ACQSTOP = 2  # stop trigger (mpxCtrlTrigger(TRIGGER_ACQSTOP))

    # CONST


class PmApiError(Exception):
    __errordict__ = {0: 'MPXERR_NOERROR: success',
                     -1: 'MPXERR_UNEXPECTED: unexpected error',
                     -2: 'MPXERR_INVALID_PARVAL: invalid param supplied',
                     -3: 'MPXERR_MEMORY_ALLOC: memory allocation error',
                     -4: 'MPXERR_BUFFER_SMALL: supplied buffer is too small',
                     -5: 'MPXERR_FILE_OPENREAD: cannot open file for reading',
                     -6: 'MPXERR_FILE_OPENWRITE: cannot open file for writing',
                     -7: 'MPXERR_FILE_READ: error while reading file',
                     -8: 'MPXERR_FILE_WRITE: error while writing to file',
                     -9: 'MPXERR_FILE_BADDATA: invalid value was read from file',
                     -10: 'MPXERR_LOCK_TIMEOUT: timeout while waiting for synchronization object',
                     -11: 'MPXERR_UNLOCK: failed to unlock sync object (caller is not lock owner)',
                     -12: 'MPXERR_FILE_NOT_FOUND: failed to locate file',
                     -13: 'MPXERR_FILE_SEEK: seek failed',
                     -100: 'MPXERR_MPXCTRL_NOTINIT: mpxctrl layer is not initialized',
                     -101: 'MPXERR_NOHWLIBFOUND: no hardware library was found',
                     -102: 'MPXERR_IDINVALID: supplied DEVID is not valid (no assigned Medipix device)',
                     -103: 'MPXERR_LOADHWLIB: failed to load one of HW library',
                     -104: 'MPXERR_HWLIBINIT: initialization of hw library error',
                     -110: 'MPXERR_MPXDEV_NOTINIT: device is not properly initialized',
                     -111: 'MPXERR_OPENCFG: open cfg file failed',
                     -112: 'MPXERR_READCFG: errors occurred while reading/parsing cfg file',
                     -113: 'MPXERR_HWINFO_SETITEM: setting interface	-specific info failed',
                     -114: 'MPXERR_HWINFO_GETITEM: getting interface	-specific info failed',
                     -115: 'MPXERR_FRAME_NOTREADY: required frame is not ready',
                     -150: 'MPXERR_ACQSTART: fail to start acquisition',
                     -151: 'MPXERR_ACQSTOP: fail to stop acquisition',
                     -152: 'MPXERR_ACQABORTED: acq aborted',
                     -153: 'MPXERR_CHECK_BUSY: fail to check busy state',
                     -154: 'MPXERR_READMATRIX: read matrix failed',
                     -155: 'MPXERR_WRITEMATRIX: write matrix failed',
                     -156: 'MPXERR_RESETMATRIX: reset matrix failed',
                     -157: 'MPXERR_TESTPULSES: test pulses sending failed',
                     -158: 'MPXERR_SETMASK: setting mask (pix. configuration) failed',
                     -159: 'MPXERR_READANALOGDAC: failed to sense DAC analog value',
                     -160: 'MPXERR_SETDACS: failed to set DACs',
                     -161: 'MPXERR_CONVSTREAM2DATA: stream to data conversion error',
                     -162: 'MPXERR_CONVDATA2STREAM: data to stream conversion error',
                     -163: 'MPXERR_CONVPSEUDO: error converting pseudorandom counter values',
                     -164: 'MPXERR_SETEXTDAC: failed to set external DAC',
                     -165: 'MPXERR_INVALIDOP: invalid operation (operation cannot be performed)',
                     -200: 'MPXERR_FRAME_NOTEXIST: frame with specified ID does not exist',
                     -201: 'MPXERR_FRAME_NOTINIT: frame was not properly initialized',
                     -202: 'MPXERR_ATTRIB_NOTFOUND: attribute was not found',
                     -203: 'MPXERR_ATTRIB_EXISTS: attribute already exists',
                     -204: 'MPXERR_INVALID_SIZE: invalid size of frame',
                     -205: 'MPXERR_DATAFILE_FORMAT: invalid format of data file',
                     -206: 'MPXERR_DESCFILE_FORMAT: invalid format of description file',
                     -207: 'MPXERR_CLOSE_PROTECT: cannot close frame, frame is protected',
                     -208: 'MPXERR_FILTER_FAILED: filter function failed',
                     -209: 'MPXERR_INCONSISTENT_DATA: inconsistence of read/parsed data detected',
                     -300: 'MPXERR_PLUGIN_NOTEXIST: referenced plugin is not registered',
                     -301: 'MPXERR_FUNC_ALREADYREG: function is already registered by this plugin',
                     -302: 'MPXERR_FUNC_NOTEXIST: function is not registered by this plugin',
                     -303: 'MPXERR_MENUITEM_ALREADYREG: menu item already exists',
                     -304: 'MPXERR_MENUITEM_NOTEXIST: specified menu item is not registered',
                     -305: 'MPXERR_EVENT_ALREADYREG: event is already registered by this plugin',
                     -306: 'MPXERR_EVENT_NOTEXIST: event is not registered by this plugin',
                     -307: 'MPXERR_FRAMEATTR_ALREADYREG: frame attribute template is already registered by this plugin',
                     -308: 'MPXERR_FRAMEATTR_NOTEXIST: frame attribute template with this name is not registered',
                     -309: 'MPXERR_FILTCHAIN_ALREADYREG: filter chain is already registered by this plugin',
                     -310: 'MPXERR_FILTCHAIN_NOTEXIST: specified filter chain does not exist',
                     -311: 'MPXERR_FILTERINST_EXIST: instance of filter with specified name already exists'
    }

    def __init__(self, value):
        print('error no %d' % value)
        self.value = self.__errordict__.get(value)

    def __str__(self):
        return repr(self.value)


# typedef struct _ExtFunctionInfo
# {
#    PluginFuncType func;                    // pointer to registered function
#    int paramInCount;                       // number of input parameters
#    int paramOutCount;                      // number of output parameters
#    ExtParamInfo paramsInfoIn[MAX_PARAM];   // input parameters infos
#    ExtParamInfo paramsInfoOut[MAX_PARAM];  // output parameters infos
#    char pluginName[NAME_LENGTH];           // plugin name
#    char functionName[NAME_LENGTH];         // function name
#    char description[DESC_LENGTH];          // function description
#    INTPTR userData;                        // custom parameter that will be used for func call
#    u32 flags;                              // combination of FUNCFLAG_XXX
#    ITEMID funcID;                          // function ID (filled by MpxManager)
#} ExtFunctionInfo;

#// structure describing one parameter of plugin function
#typedef struct _ExtParamInfo
#{
#    Data_Types type;                    // parameter type
#    int count;                          // count (for array of type)
#    char description[DESC_LENGTH];      // description string
#} ExtParamInfo;
NAME_LENGTH = 32
DESC_LENGTH = 128


class ExtParamInfo(ctypes.Structure):
    _fields_ = [('type', c_int),
                ('count', c_int),
                ('description', c_char * DESC_LENGTH)
    ]


class ExtFunctionInfo(ctypes.Structure):
    _fields_ = [('PluginFuncType', c_int),
                ('paramInCount', c_int),
                ('paramOutCount', c_int),
                ('paramInfoIn', ExtParamInfo),
                ('paramInfoOut', ExtParamInfo),
                ('pluginName', c_char * NAME_LENGTH),
                ('functionName', c_char * NAME_LENGTH),
                ('description', c_char * DESC_LENGTH),
                ('userData', c_int),
                ('flags', c_uint32),
                ('itemID', c_int)
    ]


class DevInfo(ctypes.Structure):
    _fields_ = [("pixCount", c_int),
                ("rowLen", c_int),
                ("numberOfChips", ctypes.c_int),
                ("numberOfRows", ctypes.c_int),
                ("mpxType", ctypes.c_int),
                ("chipboardID", c_char * 64),
                ("ifaceName", c_char_p),

                ("idaceType", ctypes.c_int),
                ("ifaceVendor", ctypes.c_int),
                ("ifaceSerial", ctypes.c_int),
                ("chipboardSerial", ctypes.c_int),

                ("suppAcqModes", c_uint32),
                ("suppCallback", c_bool),
                ("clockReadout", c_double),
                ("clockTimepix", c_double),
                ("timerMinVal", c_double),
                ("timerMaxVal", c_double),
                ("timerStep", c_double),
                ("maxPulseCount", c_uint32),
                ("maxPulseHeight", c_double),
                ("maxPulsePeriod", c_double),
                ("extDacMinV", c_double),
                ("extDacMaxV", c_double),
                ("extDacStep", c_double)
    ]


#FIXME Only valid for Timepix!


class PixCfgs(ctypes.Structure):
    _fields_ = [('maskBit', c_byte),
                ('testBit', c_byte),
                ('thlAdj', c_byte),
                ('mode', c_byte)
    ]


class DACDef(object):
    max = dict()
    order = dict()
    count = 0

    def __init__(self, names, precisisons, n):
        self.count = n
        for i in np.arange(self.count):
            self.max[names[i].upper()] = 2 ** precisisons[i] - 1
            self.order[names[i].upper()] = i

    def __getitem__(self, key):
        key = key.upper()
        return self.max[key], self.order[key]

    def dacnames(self):
        return self.max.keys()


class PmMgrApi(object):
    pm_root = "/Applications/Pixelman"
    mgr = None

    def __addfunc(self, funcname, restype, argtypes):
        f = getattr(self.mgr, funcname)
        f.restype = restype
        f.argtypes = argtypes

    def __init__(self, rootpath="/Applications/Pixelman", system='LX'):
        pm_root = rootpath;
        self.__class__.pm_root = rootpath;
        chdir(self.__class__.pm_root);
        if system == 'LX':
            os.chdir(self.__class__.pm_root)
            print 'Trying:', self.__class__.pm_root + '/libmpxmanager.so'
            self.mgr = CDLL(self.__class__.pm_root + '/libmpxmanager.so')
        elif system == 'Win':
            self.mgr = CDLL(self.__class__.pm_root + '/mpxmanager.dll')

        # int mgrInitManager(u32 flags, const char *pluginNames);
        self.__addfunc('mgrInitManager', c_int32, [c_uint, c_char_p])

        # int mgrExitManager();
        self.__addfunc('mgrExitManager', c_int32, [])

        # BOOL mgrIsRunning();
        self.__addfunc('mgrIsRunning', c_bool, [])


        # int mgrInvokeInUIThread(CallbackFuncType func, CBPARAM par);
        # int mgrGetCfgsPath(char path[MPX_MAX_PATH]);
        # int mgrLogMsg(const char *pluginName, const char *format, u32 flags, );
        # int mgrLogMsgV(const char *pluginName, const char *format, u32 flags, va_list argptr);
        # int mgrLogShowWindow(BOOL show);
        self.__addfunc('mgrInitManager', c_int32, [c_uint, c_char_p])

        # int mgrManagedItemsShowWindow(BOOL show);
        self.__addfunc('mgrInitManager', c_int32, [c_uint, c_char_p])

        # int mgrAddPlugin(const char *filename);
        # int mgrRegisterExtPlugin(const char *name);
        # int mgrAddMenuItem(const char *pluginName, const char *itemName, const char *menuPath, MenuFuncType func, MENUFUNCPAR param, ITEMID *menuItemID, u32 flags);
        # int mgrAddMpxMenuItem(DEVID devID, const char *pluginName, const char *itemName, const char *menuPath, MenuFuncType func, MENUFUNCPAR param, ITEMID *menuItemID, u32 flags);
        # int mgrRemoveMenuItem(ITEMID menuItemID);
        # int mgrGetMpxMenuPath(DEVID devID, char menuPath[MENU_LENGTH]);
        # int mgrGetFirstMenuItem(ITEMID *itemID, char name[MENU_LENGTH]);
        # int mgrGetNextMenuItem(ITEMID *itemID, char name[MENU_LENGTH]);
        # int mgrCallMenuItemByName(const char *name);
        # int mgrCallMenuItemByID(ITEMID itemID);
        # void mgrAddMsgHandler(MsgHandlerType handler);
        # void mgrRemoveMsgHandler(MsgHandlerType handler);
        # int mgrAddFuncItem(ExtFunctionInfo *funcInfo);
        # int mgrRemoveFuncItem(const char *pluginName, const char *functionName);
        # int mgrGetRegFirstFunc(ITEMID *funcID, ExtFunctionInfo *funcInfo);
        self.__addfunc('mgrGetRegFirstFunc', c_int, [POINTER(c_int), POINTER(ExtFunctionInfo)])
        # int mgrGetRegNextFunc(ITEMID *funcID, ExtFunctionInfo *funcInfo);
        self.__addfunc('mgrGetRegNextFunc', c_int, [POINTER(c_int), POINTER(ExtFunctionInfo)])
        # int mgrGetFuncItemID(ITEMID funcID, ExtFunctionInfo *extFuncInfo);
        # int mgrGetFuncItem(const char *pluginName, const char *functionName, ExtFunctionInfo *extFuncInfo);
        # int mgrCallFuncItem(const char *pluginName, const char *functionName, byte *in, byte *out);
        # int mgrAddCBEvent(ExtCBEventInfo *cbEventInfo, ITEMID *cbEventID);
        # int mgrRemoveCBEvent(const char *pluginName, const char *cbEventName);
        # int mgrGetRegFirstCBEvent(ITEMID *cbEventID, ExtCBEventInfo *extCBEventInfo);
        # int mgrGetRegNextCBEvent(ITEMID *cbEventID, ExtCBEventInfo *extCBEventInfo);
        # int mgrSetCBEvent(ITEMID ID, CBPARAM par);
        # int mgrRegisterCallback(const char *pluginName, const char *cbEventName, CallbackFuncType callback, INTPTR userData);
        # int mgrUnregisterCallback(const char *pluginName, const char *cbEventName, CallbackFuncType callback, INTPTR userData);
        # int mgrAddFrameAttribTempl(ExtFrameAttribInfo *attribInfo);
        # int mgrRemoveFrameAttribTempl(const char *attribName);
        # int mgrCreateFilterChain(const char *pluginName, const char *filterChainName, ITEMID *filterChainID);
        # int mgrRemoveFilterChain(ITEMID filterChainID);
        # int mgrAddToFilterChain(ITEMID filterChainID, ITEMID funcID, u32 order);
        # int mgrRemoveFromFilterChain(ITEMID filterChainID, u32 order);
        # int mgrGetFilteredFrame(ITEMID filterChainID, FRAMEID inID, FRAMEID *outID);
        # int mgrGetFirstFilterChain(ITEMID *filterChainID, ExtFilterChainInfo *filterChainInfo);
        # int mgrGetNextFilterChain(ITEMID *filterChainID, ExtFilterChainInfo *filterChainInfo);
        # int mgrGetFilterChainInfo(ITEMID filterChainID, ExtFilterChainInfo *filterChainInfo);
        # int mgrCreateFilterInst(ITEMID filterID, const char *name, ITEMID *instID);
        # int mgrDeleteFilterInst(ITEMID instID);
        # int mgrGetFirstFilterInst(ITEMID filterID, ITEMID *instID, char name[NAME_LENGTH]);
        # int mgrGetNextFilterInst(ITEMID filterID, ITEMID *instID, char name[NAME_LENGTH]);
        # int mgrSetFilterPar(ITEMID instID, int idx, byte *data, int dataSize);
        # int mgrGetFilterPar(ITEMID instID, int idx, ItemInfo *info, int *dataSize);
        # // frame control
        # //
        # int mgrCreateFrame(FRAMEID *frameID, u32 width, u32 height, int type, const char *creatorName);
        self.__addfunc('mgrCreateFrame', c_int32, [POINTER(c_uint), c_uint, c_uint, c_int, c_char_p])
        # int mgrGetFrameCount(const char *fileName, int *count);
        # int mgrLoadFrame(FRAMEID *frameID, const char *fileName, int idx);
        # int mgrSaveFrame(FRAMEID frameID, const char *fileName, u32 flags);
        # int mgrDuplicateFrame(FRAMEID origID, FRAMEID *newID);
        # int mgrGetFirstFrame(FRAMEID *frameID);
        # int mgrGetNextFrame(FRAMEID *frameID);
        # int mgrOpenFrame(FRAMEID frameID, u32 *refCount);
        # int mgrCloseFrame(FRAMEID frameID, u32 *refCount);
        # int mgrLockFrame(FRAMEID frameID, u32 timeout);
        # int mgrUnlockFrame(FRAMEID frameID);
        #
        # int mgrGetFrameType(FRAMEID frameID, Data_Types *type);
        # int mgrSetFrameType(FRAMEID frameID, Data_Types type);
        # int mgrGetFrameSize(FRAMEID frameID, u32 *width, u32 *height);
        # int mgrSetFrameSize(FRAMEID frameID, u32 width, u32 height);
        # int mgrSetFrameData(FRAMEID frameID, byte *buffer, u32 size);
        # int mgrGetFrameData(FRAMEID frameID, byte *buffer, u32 *size, Data_Types type);
        # int mgrGetLockedFrameBuff(FRAMEID frameID, byte **buffer, u32 *size, u32 timeout);
        # int mgrLoadFrameData(FRAMEID frameID, const char *fileName, u32 flags);
        #
        # int mgrSetFrameName(FRAMEID frameID, const char *name);
        # int mgrGetFrameName(FRAMEID frameID, char name[NAME_LENGTH]);
        # int mgrSetFrameCreatorName(FRAMEID frameID, const char *name);
        # int mgrGetFrameCreatorName(FRAMEID frameID, char name[NAME_LENGTH]);
        # int mgrSetFrameLogPath(FRAMEID frameID, const char *path);
        # int mgrGetFrameLogPath(FRAMEID frameID, char path[MPX_MAX_PATH]);
        # int mgrGetFrameFileName(FRAMEID frameID, char path[MPX_MAX_PATH]);
        # int mgrAddFrameAttrib(FRAMEID frameID, const char *name, const char *desc, Data_Types type, const byte *data, u32 count);
        # int mgrSetFrameAttrib(FRAMEID frameID, const char *name, byte *data, u32 size);
        # int mgrGetFrameAttrib(FRAMEID frameID, const char *name, byte *data, u32 *size, Data_Types *type);
        # int mgrRemoveAttrib(FRAMEID frameID, const char *name);
        # int mgrRemoveAllAttribs(FRAMEID frameID);
        # int mgrGetFrameFirstAttrib(FRAMEID frameID, ITEMID *itemID, ExtFrameAttrib *attrib);
        # int mgrGetFrameNextAttrib(FRAMEID frameID, ITEMID *itemID, ExtFrameAttrib *attrib);
        #
        # int mgrCreateSubframe(FRAMEID frameID, int *subframeIdx, u32 width, u32 height, int flags);
        # int mgrGetSubframeCount(FRAMEID frameID, int *subframeCount);
        # int mgrGetSubframeType(FRAMEID frameID, int subframeIdx, Data_Types *type);
        # int mgrSetSubframeType(FRAMEID frameID, int subframeIdx, Data_Types type);
        # int mgrGetSubframeSize(FRAMEID frameID, int subframeIdx, u32 *width, u32 *height);
        # int mgrSetSubframeSize(FRAMEID frameID, int subframeIdx, u32 width, u32 height);
        # int mgrSetSubframeData(FRAMEID frameID, int subframeIdx, byte *buffer, u32 size);
        # int mgrGetSubframeData(FRAMEID frameID, int subframeIdx, byte *buffer, u32 *size, Data_Types type);
        # int mgrGetLockedSubframeBuff(FRAMEID frameID, int subframeIdx, byte **buffer, u32 *size, u32 timeout);
        # int mgrSetSubframeName(FRAMEID frameID, int subframeIdx, const char *name);
        # int mgrGetSubframeName(FRAMEID frameID, int subframeIdx, char name[MPX_MAX_PATH]);
        #
        # int mgrGetServiceFrame(DEVID devID, u32 type, FRAMEID *frameID);
        #
        # // functions provided from MpxCtrl dll (mpxCtrl prefix)
        # //
        # int mpxCtrlGetFirstMpx(DEVID *devID, int *count = 0);
        self.__addfunc('mpxCtrlGetFirstMpx', c_int, [POINTER(c_uint), POINTER(c_int)])

        # int mpxCtrlGetNextMpx(DEVID *devID);
        self.__addfunc('mpxCtrlGetNextMpx', c_int, [POINTER(c_uint)])

        # int mpxCtrlFindNewMpxs();
        self.__addfunc('mpxCtrlFindNewMpxs', c_int, [])

        # int mpxCtrlReconnectMpx(DEVID devID);
        self.__addfunc('mpxCtrlReconnectMpx', c_int, [c_uint])
        #
        # int mpxCtrlGetHwInfoCount(DEVID devID, int *count);
        self.__addfunc('mpxCtrlGetHwInfoCount', c_int, [c_uint, POINTER(c_int)])

        # int mpxCtrlGetHwInfoItem(DEVID devID, int index, HwInfoItem *infoItem, int *dataSize);
        # int mpxCtrlSetHwInfoItem(DEVID devID, int index, byte *data, int dataSize);
        #
        # //
        # int mpxCtrlSetCustomName(DEVID devID, const char *name);
        # int mpxCtrlGetCustomName(DEVID devID, char name[NAME_LENGTH]);
        # int mpxCtrlTryLockDevice(DEVID devID, BOOL *success, u32 timeout = 0);
        # int mpxCtrlReleaseDevice(DEVID devID);
        # int mpxCtrlGetLockOwnerID(DEVID devID, u32 *id);
        #
        # int mpxCtrlReviveMpxDevice(DEVID devID);
        self.__addfunc('mpxCtrlReviveMpxDevice', c_int, [c_uint])

        # int mpxCtrlSaveMpxCfg(DEVID devID, const char *fileName);
        self.__addfunc('mpxCtrlSaveMpxCfg', c_int, [c_uint, c_char_p])

        # int mpxCtrlLoadMpxCfg(DEVID devID, const char *fileName);
        self.__addfunc('mpxCtrlLoadMpxCfg', c_int, [c_uint, c_char_p])

        # int mpxCtrlSaveMpxCfgAsDefault(DEVID devID);
        self.__addfunc('mpxCtrlSaveMpxCfgAsDefault', c_int, [c_uint])
        #
        # // set/get acquisition setting
        # //
        # int mpxCtrlSetDevSpecAcqPars(DEVID devID, byte *pars, u32 size);
        # int mpxCtrlGetDevSpecAcqPars(DEVID devID, byte *pars, u32 size);
        # int mpxCtrlSetPolarity(DEVID devID, BOOL positive);
        self.__addfunc('mpxCtrlSetPolarity', c_int, [c_uint, c_bool])

        # int mpxCtrlGetPolarity(DEVID devID, BOOL *positive);
        self.__addfunc('mpxCtrlGetPolarity', c_int, [c_uint, POINTER(c_bool)])

        # int mpxCtrlSetAcqMode(DEVID devID, int mode);
        self.__addfunc('mpxCtrlSetAcqMode', c_int, [c_uint, c_int])

        # int mpxCtrlGetAcqMode(DEVID devID, int *mode);
        self.__addfunc('mpxCtrlGetAcqMode', c_int, [c_uint, POINTER(c_int)])

        # int mpxCtrlSetHwTimer(DEVID devID, int state);
        # int mpxCtrlGetHwTimer(DEVID devID, int *state);
        # int mpxCtrlSetDACsDefault(DEVID devID);

        # int mpxCtrlSetDACs(DEVID devID, DACTYPE dacVals[], int size, int chipNumber);
        self.__addfunc('mpxCtrlSetDACs', c_int, [c_uint, POINTER(c_ushort), c_int, c_int])


        # int mpxCtrlGetDACs(DEVID devID, DACTYPE dacVals[], int size, int chipNumber);
        self.__addfunc('mpxCtrlGetDACs', c_int, [c_uint, POINTER(c_ushort), c_int, c_int])

        # int mpxCtrlGetSingleDACAnalog(DEVID devID, double dacVals[], int size, int dacNumber, int chipNumber, int senseCount);
        self.__addfunc('mpxCtrlGetSingleDACAnalog', c_int, [c_uint, POINTER(c_double), c_int, c_int, c_int])

        # int mpxCtrlGetDACsAnalog(DEVID devID, double dacVals[], int size, int chipNumber);
        self.__addfunc('mpxCtrlGetDACsAnalog', c_int, [c_uint, POINTER(c_double), c_int, c_int])

        # int mpxCtrlRefreshDACs(DEVID devID);

        # int mpxCtrlGetDACsNames(DEVID devID, const char * const **names, const int **precisions, int *size);
        self.__addfunc('mpxCtrlGetDACsNames', c_int,
                       [c_uint, POINTER(POINTER(c_char_p)), POINTER(POINTER(c_int)), POINTER(c_int)])

        # int mpxCtrlSetExtDAC(DEVID devID, int dacNumber, double value);
        # int mpxCtrlGetExtDAC(DEVID devID, int *dacNumber, double *value);
        #
        # int mpxCtrlSetPixelsCfg(DEVID devID, byte pixCfgs[], int size, int chipNumber);
        self.__addfunc('mpxCtrlSetPixelsCfg', c_int, [c_int, POINTER(c_byte), c_int, c_int])
        # int mpxCtrlGetPixelsCfg(DEVID devID, byte pixCfgs[], int size, int chipNumber);
        self.__addfunc('mpxCtrlGetPixelsCfg', c_int, [c_int, POINTER(c_byte), c_int, c_int])
        # int mpxCtrlResetPixelsCfg(DEVID devID, int chipNumber);
        # int mpxCtrlSetSuperMatrixPixCfg(DEVID devID, byte pixCfgs[], int size);
        # int mpxCtrlGetSuperMatrixPixCfg(DEVID devID, byte pixCfgs[], int size);
        # int mpxCtrlRefreshPixelsCfg(DEVID devID);
        # int mpxCtrlSetSuppressMasked(DEVID devID, BOOL suppress);
        # int mpxCtrlGetSuppressMasked(DEVID devID, BOOL *suppress);
        # int mpxCtrlSetAutoConvToSM(DEVID devID, BOOL enable);
        # int mpxCtrlGetAutoConvToSM(DEVID devID, BOOL *enable);
        # int mpxCtrlConvToSuperMatrix(DEVID devID, const byte *chipByChip, byte *superMatrix, u32 buffSize, Data_Types buffType);
        # int mpxCtrlConvFromSuperMatrix(DEVID devID, const byte *superMatrix, byte *chipByChip, u32 buffSize, Data_Types buffType);
        #
        # int mpxCtrlLoadPixelsCfg(DEVID devID, const char *fileName, BOOL loadDacs);
        self.__addfunc('mpxCtrlLoadPixelsCfg', c_int, [c_uint, c_char_p, c_bool])

        # int mpxCtrlSavePixelsCfg(DEVID devID, const char *fileName, BOOL saveDacs);
        self.__addfunc('mpxCtrlSavePixelsCfg', c_int, [c_uint, c_char_p, c_bool])

        # int mpxCtrlLoadPixelsCfgAscii(DEVID devID, const char *fileName, int part, BOOL loadDacs);
        self.__addfunc('mpxCtrlLoadPixelsCfgAscii', c_int, [c_uint, c_char_p, c_int, c_bool])

        # int mpxCtrlSavePixelsCfgAscii(DEVID devID, const char *fileName, int part, BOOL saveDacs);
        self.__addfunc('mpxCtrlSavePixelsCfgAscii', c_int, [c_uint, c_char_p, c_int, c_bool])
        #
        # // acquisition control
        # //
        # int mpxCtrlPerformIntegralAcq(DEVID devID, int numberOfAcq, double timeOfEachAcq, u32 fileFlags = 0, const char *fileName = 0);
        # int mpxCtrlPerformFrameAcq(DEVID devID, int numberOfFrames, double timeOfEachAcq, u32 fileFlags = 0, const char *fileName = 0);
        self.__addfunc('mpxCtrlPerformFrameAcq', c_int, [c_uint, c_int, c_double, c_uint32, c_char_p])

        # int mpxCtrlPerformTestPulseAcq(DEVID devID, int spacing, double *pulseHeight, double period, u32 pulseCount, u32 *manual, BOOL manualTPBits);
        self.__addfunc('mpxCtrlPerformTestPulseAcq', c_int,
                       [c_uint, c_int, POINTER(c_double), c_double, c_uint32, POINTER(c_uint32), c_bool])

        # int mpxCtrlPerformDigitalTest(DEVID devID, u32 *goodPixels, FRAMEID *frameID, BOOL show, double delay);
        self.__addfunc('mpxCtrlPerformDigitalTest', c_int,
                       [c_uint, POINTER(c_uint32), POINTER(c_uint32), c_bool, c_double])

        # int mpxCtrlAbortOperation(DEVID devID);
        self.__addfunc('mpxCtrlAbortOperation', c_int, [])

        # int mpxCtrlTrigger(DEVID devID, int trigger);
        self.__addfunc('mpxCtrlTrigger', c_int, [c_uint, c_int])
        #
        # // buffer control
        # //
        # int mpxCtrlCloseFrames(DEVID devID);
        self.__addfunc('mpxCtrlCloseFrames', c_int, [c_uint])

        # int mpxCtrlGetFrame16(DEVID devID, i16 *buffer, u32 size, u32 frameNumber);
        self.__addfunc('mpxCtrlGetFrame16', c_int, [c_uint, POINTER(c_int16), c_uint32, c_uint32])

        # int mpxCtrlGetFrame32(DEVID devID, u32 *buffer, u32 size, u32 frameNumber);
        self.__addfunc('mpxCtrlGetFrame32', c_int, [c_uint, POINTER(c_int32), c_uint32, c_uint32])

        # int mpxCtrlGetFrameDouble(DEVID devID, double *buffer, u32 size, u32 frameNumber);
        self.__addfunc('mpxCtrlGetFrameDouble', c_int, [c_uint, POINTER(c_double), c_uint32, c_uint32])

        # int mpxCtrlSaveFrame(DEVID devID, const char *fileName, int frameNumber, u32 flags);
        self.__addfunc('mpxCtrlSaveFrame', c_int, [c_uint, c_char_p, c_int, c_uint32])

        # int mpxCtrlGetFrameAttrib(DEVID devID, int frameNumber, const char *name, byte *value, u32 *size, Data_Types *type);
        # int mpxCtrlGetFrameID(DEVID devID, int frameNumber, FRAMEID *frameID);
        #
        # // info functions
        # int mpxCtrlGetDevInfo(DEVID devID, DevInfo *devInfo);
        self.__addfunc('mpxCtrlGetDevInfo', c_int, [c_uint, POINTER(DevInfo)])
        # int mpxCtrlGetMedipixInfo(DEVID devID, int *numberOfChips, int *numberOfRows, char chipBoardID[MPX_MAX_CHBID] = 0, char ifaceName[MPX_MAX_IFACENAME] = 0);
        self.__addfunc('mpxCtrlGetMedipixInfo', c_int, [c_uint, POINTER(c_int), POINTER(c_int), c_char_p, c_char_p])

        # int mpxCtrlGetAcqInfo(DEVID devID, int *acqNumber, int *acqTotalCount, int *acqType, u32 *frameFilled);
        self.__addfunc('mpxCtrlGetAcqInfo', c_int,
                       [c_uint, POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_uint32)])

    # int mpxCtrlGetInfoMsg(DEVID devID, int *msgType, const char **msg);
    ##################################################################################




    def __checkError(self, idx, *args):
        if (idx != 0):
            raise PmApiError(idx)
            # int mgrInitManager(u32 flags, const char *pluginNames);

    def mgrInitManager(self, flags=3, pluginNames=0):
        if (pluginNames == 0):
            pluginNames = c_char_p()
        r = self.mgr.mgrInitManager(flags, pluginNames)
        self.__checkError(r)
        return r

    # int mgrExitManager();
    def mgrExitManager(self):
        r = self.mgr.mgrExitManager()
        self.__checkError(r)
        return r

    # BOOL mgrIsRunning();
    def mgrIsRunning(self):
        return self.mgr.mgrIsRunning()

    # int mgrLogShowWindow(BOOL show);
    def mgrLogShowWindow(self, show):
        r = self.mgr.mgrLogShowWindow(show)
        self.__checkError(r)
        return r

    # int mgrManagedItemsShowWindow(BOOL show);
    def mgrManagedItemsShowWindow(self, show):
        r = self.mgr.mgrManagedItemsShowWindow(show)
        self.__checkError(r)
        return r

    # int mpxCtrlGetFirstMpx(DEVID *devID, int *count = 0);
    def mpxCtrlGetFirstMpx(self):
        devID = c_uint32()
        count = c_int()
        r = self.mgr.mpxCtrlGetFirstMpx(byref(devID), byref(count))
        self.__checkError(r)
        return c_int(devID.value).value, count.value


    # int mpxCtrlGetNextMpx(DEVID *devID);
    def mpxCtrlGetNextMpx(self, devID):
        id = c_uint32(devID)
        r = self.mgr.mpxCtrlGetNextMpx(byref(id))
        if (r != 0):
            print('no more devices found')
        return devID, r

    # int mpxCtrlFindNewMpxs();
    def mpxCtrlFindNewMpxs(self):
        r = self.mgr.mpxCtrlFindNewMpxs()
        self.__checkError(r)
        return r

    # int mpxCtrlReconnectMpx(DEVID devID);
    def mpxCtrlReconnectMpx(self, devID):
        r = self.mgr.mpxCtrlReconnectMpx(devID)
        self.__checkError(r)
        return r

    # int mpxCtrlGetHwInfoCount(DEVID devID, int *count);
    def mpxCtrlGetHwInfoCount(self, devID):
        count = c_int()
        r = self.mgr.mpxCtrlGetHwInfoCount(devID, byref(count))
        self.__checkError(r)
        return count.value

    # int mpxCtrlReviveMpxDevice(DEVID devID);
    def mpxCtrlReviveMpxDevice(self, devID):
        r = self.mgr.mpxCtrlReviveMpxDevice(devID)
        self.__checkError(r)
        return r

    # int mpxCtrlSaveMpxCfg(DEVID devID, const char *fileName);
    def mpxCtrlSaveMpxCfg(self, devID, filename):
        r = self.mgr.mpxCtrlSaveMpxCfg(devID, filename)
        self.__checkError(r)
        return r

    # int mpxCtrlLoadMpxCfg(DEVID devID, const char *fileName);
    def mpxCtrlLoadMpxCfg(self, devID, filename):
        r = self.mgr.mpxCtrlLoadMpxCfg(devID, filename)
        self.__checkError(r)
        return r

    # int mpxCtrlSaveMpxCfgAsDefault(DEVID devID);
    def mpxCtrlSaveMpxCfgAsDefault(self, devID):
        r = self.mgr.mpxCtrlSaveMpxCfgAsDefault(devID)
        self.__checkError(r)
        return r

    # int mpxCtrlSetPolarity(DEVID devID, BOOL positive);
    def mpxCtrlSetPolarity(self, devID, pol):
        if (pol.__class__ != bool):
            raise PmApiError(-2)
        r = self.mgr.mpxCtrlSetPolarity(devID, pol)
        self.__checkError(r)
        return r

    # int mpxCtrlGetPolarity(DEVID devID, BOOL *positive);
    def mpxCtrlGetPolarity(self, devID):
        pol = c_bool()
        r = self.mgr.mpxCtrlGetPolarity(devID, byref(pol))
        self.__checkError(r)
        return pol

    # int mpxCtrlSetAcqMode(DEVID devID, int mode);
    def mpxCtrlSetAcqMode(self, devID, mode):
        r = self.mgr.mpxCtrlSetAcqMode(devID, mode)
        self.__checkError(r)
        return r

    # int mpxCtrlGetAcqMode(DEVID devID, int *mode);
    def mpxCtrlGetAcqMode(self, devID):
        mode = c_int()
        r = self.mgr.mpxCtrlGetAcqMode(devID, byref(mode))
        return mode.value

    # int mpxCtrlSetHwTimer(DEVID devID, int state);
    # int mpxCtrlGetHwTimer(DEVID devID, int *state);
    # int mpxCtrlSetDACsDefault(DEVID devID);

    # int mpxCtrlSetDACs(DEVID devID, DACTYPE dacVals[], int size, int chipNumber);
    def mpxCtrlSetDACs(self, devID, dacVals, asize, chipNumber=0):
        # expecting ndarray
        if not ( (dacVals.__class__ == np.ndarray) | (dacVals.__class__ == np.array) ):
            raise PmApiError(-2)
        x = cast(dacVals.ctypes.data, POINTER(c_ushort))
        r = self.mgr.mpxCtrlSetDACs(devID, x, asize, chipNumber)
        self.__checkError(r)
        return r

    # int mpxCtrlGetDACs(DEVID devID, DACTYPE dacVals[], int size, int chipNumber);
    def mpxCtrlGetDACs(self, devID, size, chipNumber=0):

        dacs = np.ndarray([size], c_ushort)
        x = cast(dacs.ctypes.data, POINTER(c_ushort))
        r = self.mgr.mpxCtrlGetDACs(devID, x, size, chipNumber)
        self.__checkError(r)
        return dacs

    # int mpxCtrlGetSingleDACAnalog(DEVID devID, double dacVals[], int size, int dacNumber, int chipNumber, int senseCount);
    def mpxCtrlGetSingleDACAnalog(self, devID, size, dacNumber, chipNumber=0, senseCount=3):
        dacs = np.ndarray([size], c_double)
        x = cast(dacs.ctypes.data, POINTER(c_double))

        r = self.mgr.mpxCtrlGetSingleDACAnalog(devID, x, size, dacNumber, chipNumber, senseCount)
        self.__checkError(r)
        return dacs

    # int mpxCtrlGetDACsAnalog(DEVID devID, double vals[], int size, int chipNumber);
    def mpxCtrlGetDACsAnalog(self, devID, size, chipNumber=0, senseCount=3):
        vals = np.ndarray([size], c_double)
        x = cast(vals.ctypes.data, POINTER(c_double))
        r = self.mgr.mpxCtrlGetDACsAnalog(devID, x, size, chipNumber)
        self.__checkError(r)
        return vals


    # int mpxCtrlRefreshDACs(DEVID devID);

    # int mpxCtrlGetDACsNames(DEVID devID, const char * const **names, const int **precisions, int *size);
    def mpxCtrlGetDACsNames(self, devID):
        names = byref(POINTER(c_char_p)())
        precisions = byref(POINTER(c_int)())
        n = byref(c_int())
        r = self.mgr.mpxCtrlGetDACsNames(devID, names, precisions, n)
        self.__checkError(r)
        return DACDef(names._obj, precisions._obj, n._obj.value)

    # int mpxCtrlLoadPixelsCfg(DEVID devID, const char *fileName, BOOL loadDacs);
    def mpxCtrlLoadPixelsCfg(self, devID, filename, loadDacs=True):
        r = self.mgr.mpxCtrlLoadPixelsCfg(devID, filename, loadDacs)
        self.__checkError(r)
        return r

    # int mpxCtrlSavePixelsCfg(DEVID devID, const char *fileName, BOOL saveDacs);
    def mpxCtrlSavePixelsCfg(self, devID, filename, saveDacs=True):
        r = self.mgr.mpxCtrlSavePixelsCfg(devID, filename, saveDacs)
        self.__checkError(r)
        return r

    # int mpxCtrlLoadPixelsCfgAscii(DEVID devID, const char *fileName, int part, BOOL loadDacs);
    def mpxCtrlLoadPixelsCfgAscii(self, devID, filename, part, loadDacs=True):
        #define PIXCFG_MASK     1
        #define PIXCFG_TEST     2
        #define PIXCFG_THL      3
        #define PIXCFG_THH      4
        #define PIXCFG_MODE     5
        #define PIXCFG_GAIN     6

        r = self.mgr.mpxCtrlSavePixelsCfg(devID, filename, part, loadDacs)
        self.__checkError(r)
        return r

    # int mpxCtrlSavePixelsCfgAscii(DEVID devID, const char *fileName, int part, BOOL saveDacs);
    def mpxCtrlSavePixelsCfgAscii(self, devID, filename, part, saveDacs=True):
        r = self.mgr.mpxCtrlSavePixelsCfg(devID, filename, part, saveDacs)
        self.__checkError(r)
        return r

    # int mpxCtrlPerformIntegralAcq(DEVID devID, int numberOfAcq, double timeOfEachAcq, u32 fileFlags = 0, const char *fileName = 0);
    # int mpxCtrlPerformFrameAcq(DEVID devID, int numberOfFrames, double timeOfEachAcq, u32 fileFlags = 0, const char *fileName = 0);
    def mpxCtrlPerformFrameAcq(self, devID, numberOfFrames, timeOfEachAcq, fileFlags=PmMgrApiConst.FSAVE_I16,
                               filename=None):

        #define FSAVE_BINARY        0x0001      // save in binary format
        #define FSAVE_ASCII         0x0002      // save in ASCII format
        #define FSAVE_APPEND        0x0004      // append frame to existing file if exists (multiframe)
        #define FSAVE_I16           0x0010      // save as 16bit integer
        #define FSAVE_U32           0x0020      // save as unsigned 32bit integer
        #define FSAVE_DOUBLE        0x0040      // save as double
        #define FSAVE_NODESCFILE    0x0100      // do not save description file
        #define FSAVE_SPARSEXY      0x1000      // save only nonzero position in [x y count] format
        #define FSAVE_SPARSEX       0x2000      // save only nonzero position in [x count] format
        #define FSAVE_NOFILE        0x8000      // frame will not be saved :)
        if (filename == None) | (filename == 0):
            fileFlags = 0
            filename = cast(None, c_char_p)
        r = self.mgr.mpxCtrlPerformFrameAcq(devID, numberOfFrames, timeOfEachAcq, fileFlags, filename)
        self.__checkError(r)
        return r


    # int mpxCtrlPerformTestPulseAcq(DEVID devID, int spacing, double *pulseHeight, double period, u32 pulseCount, u32 *manual, BOOL manualTPBits);
    def mpxCtrlPerformTestPulseAcq(self, devID, spacing=2, pulseHeight=0.5, period=128.0, pulseCount=1000, manual=None,
                                   manualTPBits=False):
        p_pulseHeight = byref(c_double(pulseHeight));
        #p_manual = byref(c_uint32(manual));
        #FIXME Only enables automatical test pulses        
        p_manual = None
        r = self.mgr.mpxCtrlPerformTestPulseAcq(devID, spacing, p_pulseHeight, period, pulseCount, p_manual,
                                                manualTPBits)
        self.__checkError(r)
        return r

    # int mpxCtrlPerformDigitalTest(DEVID devID, u32 *goodPixels, FRAMEID *frameID, BOOL show, double delay);
    def mpxCtrlPerformDigitalTest(self, devID, show=True, delay=0.0):
        goodPixels = c_uint32()
        frameID = c_uint32()
        r = self.mgr.mpxCtrlPerformDigitalTest(devID, byref(goodPixels), byref(frameID), show, delay)
        self.__checkError(r)
        return c_int(goodPixels.value).value, c_int(frameID.value).value


    # int mpxCtrlAbortOperation(DEVID devID);
    def mpxCtrlAbortOperation(self, devID):
        r = self.mgr.mpxCtrlAbortOperation(devID)
        self.__checkError(r)
        return r

    # int mpxCtrlTrigger(DEVID devID, int trigger);
    def mpxCtrlTrigger(self, devID, trigger=PmMgrApiConst.TRIGGER_ACQSTART):
        #define TRIGGER_ACQSTART            1   // start trigger (mpxCtrlTrigger(TRIGGER_ACQSTART))
        #define TRIGGER_ACQSTOP             2   // stop trigger (mpxCtrlTrigger(TRIGGER_ACQSTOP))
        r = self.mgr.mpxCtrlTrigger(devID, trigger)
        self.__checkError(r)
        return r

    # // buffer control
    # //

    # int mgrCreateFrame(FRAMEID *frameID, u32 width, u32 height, int type, const char *creatorName);
    def mgrCreateFrame(self, width=256, height=256, ftype=PmMgrApiConst.FSAVE_I16 | PmMgrApiConst.TYPE_I16,
                       creatorName='python'):
        #===============================================================================
        #         #    TYPE_BOOL   = 0,        // C bool value (int)
        #         #    TYPE_CHAR   = 1,        // signed char
        #         #    TYPE_UCHAR  = 2,        // unsigned char
        #         #    TYPE_BYTE   = 3,        // byte (unsigned char)
        #         #    TYPE_I16    = 4,        // signed short
        #         #    TYPE_U16    = 5,        // unsigned short
        #         #    TYPE_I32    = 6,        // int
        #         #    TYPE_U32    = 7,        // unsigned int
        #         #    TYPE_FLOAT  = 8,        // float
        #         #    TYPE_DOUBLE = 9,        // double
        #         #    TYPE_STRING = 10,       // zero terminated string
        #         #    TYPE_LAST   = 11,       // border
        #         #define FCREATE_ZERO        0x0100      // created frame will be filled with zeros
        #===============================================================================

        frameid = c_uint()
        r = self.mgr.mgrCreateFrame(byref(frameid), width, height, ftype, creatorName)
        self.__checkError(r)
        return frameid.value

    # int mpxCtrlCloseFrames(DEVID devID);
    def mpxCtrlCloseFrames(self, devID):
        r = self.mgr.mpxCtrlCloseFrames(devID)
        self.__checkError(r)
        return r

    # int mpxCtrlGetFrame16(DEVID devID, i16 *buffer, u32 size, u32 frameNumber);
    def mpxCtrlGetFrame16(self, devID, size=[256, 256], frameNumber=0):
        buffer = np.ndarray(size, c_int16)
        x = cast(buffer.ctypes.data, POINTER(c_int16))
        r = self.mgr.mpxCtrlGetFrame16(devID, x, np.prod(size), frameNumber)
        self.__checkError(r)
        return buffer

    # int mpxCtrlGetFrame32(DEVID devID, u32 *buffer, u32 size, u32 frameNumber);
    def mpxCtrlGetFrame32(self, devID, size=[256, 256], frameNumber=0):
        buffer = np.ndarray(size, c_int32)
        x = cast(buffer.ctypes.data, POINTER(c_int32))
        r = self.mgr.mpxCtrlGetFrame32(devID, x, np.prod(size), frameNumber)
        self.__checkError(r)
        return buffer


    # int mpxCtrlGetFrameDouble(DEVID devID, double *buffer, u32 size, u32 frameNumber);
    def mpxCtrlGetFrameDouble(self, devID, size=[256, 256], frameNumber=0):
        buffer = np.ndarray(size, c_double)
        x = cast(buffer.ctypes.data, POINTER(c_double))
        r = self.mgr.mpxCtrlGetFrameDouble(devID, x, np.prod(size), frameNumber)
        self.__checkError(r)
        return buffer

    # int mpxCtrlSaveFrame(DEVID devID, const char *fileName, int frameNumber, u32 flags);
    def mpxCtrlSaveFrame(self, devID, filename, frameNumber=0,
                         flags=PmMgrApiConst.FSAVE_I16 | PmMgrApiConst.FSAVE_ASCII):
        #define FSAVE_BINARY        0x0001      // save in binary format
        #define FSAVE_ASCII         0x0002      // save in ASCII format
        #define FSAVE_APPEND        0x0004      // append frame to existing file if exists (multiframe)
        #define FSAVE_I16           0x0010      // save as 16bit integer
        #define FSAVE_U32           0x0020      // save as unsigned 32bit integer
        #define FSAVE_DOUBLE        0x0040      // save as double
        #define FSAVE_NODESCFILE    0x0100      // do not save description file
        #define FSAVE_SPARSEXY      0x1000      // save only nonzero position in [x y count] format
        #define FSAVE_SPARSEX       0x2000      // save only nonzero position in [x count] format
        #define FSAVE_NOFILE        0x8000      // frame will not be saved :)
        r = self.mgr.mpxCtrlSaveFrame(devID, filename, frameNumber, flags)
        self.__checkError(r)
        return r

    # // info functions
    # int mpxCtrlGetDevInfo(DEVID devID, DevInfo *devInfo);
    def mpxCtrlGetDevInfo(self, devID):
        info = DevInfo();
        r = self.mgr.mpxCtrlGetDevInfo(devID, byref(info))
        self.__checkError(r)
        return info

    # mgrGetRegFirstFunc
    def mgrGetRegFirstFunc(self):
        funcID = c_int()
        functionInfo = ExtFunctionInfo()
        r = self.mgr.mgrGetRegFirstFunc(byref(funcID), byref(functionInfo))
        self.__checkError(r)
        return funcID, functionInfo

    # mgrGetRegFirstFunc
    def mgrGetRegNextFunc(self):
        funcID = c_int()
        functionInfo = ExtFunctionInfo()
        r = self.mgr.mgrGetRegNextFunc(byref(funcID), byref(functionInfo))
        self.__checkError(r)
        return funcID, functionInfo

    # int mpxCtrlGetMedipixInfo(DEVID devID, int *numberOfChips,
    #int *numberOfRows, char chipBoardID[MPX_MAX_CHBID] = 0, char ifaceName[MPX_MAX_IFACENAME] = 0);
    def mpxCtrlGetMedipixInfo(self, devID):
        numberOfChips = c_int()
        numberOfRows = c_int()
        chipid = create_string_buffer(MPX_MAX_CHBID)
        ifaceName = create_string_buffer(MPX_MAX_IFACENAME)
        r = self.mgr.mpxCtrlGetMedipixInfo(devID, byref(numberOfChips), byref(numberOfRows), chipid, ifaceName)
        self.__checkError(r)
        return numberOfChips.value, numberOfRows.value, chipid.value, ifaceName.value

    # int mpxCtrlGetAcqInfo(DEVID devID, int *acqNumber, int *acqTotalCount, int *acqType, u32 *frameFilled);
    def mpxCtrlGetAcqInfo(self, devID):
        acqNumber = c_int()
        acqTotalCount = c_int()
        acqType = c_int()
        frameFilled = c_uint32()
        r = self.mgr.mpxCtrlGetAcqInfo(devID, byref(acqNumber), byref(acqTotalCount), byref(acqType),
                                       byref(frameFilled))
        self.__checkError(r)
        return acqNumber.value, acqTotalCount.value, acqType.value, frameFilled.value


    # int mpxCtrlGetPixelsCfg(DEVID devID, byte pixCfgs[], int size, int chipNumber);
    def mpxCtrlGetPixelsCfg(self, devID, chipType):
        if chipType == 5:
            size = c_int(65536 * 2)
            chipNumber = c_int(0)  #use from info
            data = np.ndarray([65536], c_uint16)
        else:
            size = c_int(65536)  #use pix count?
            chipNumber = c_int(0)  #use from info
            data = np.ndarray([65536], c_ubyte)
        x = cast(data.ctypes.data, POINTER(c_byte))
        r = self.mgr.mpxCtrlGetPixelsCfg(devID, x, size, chipNumber)
        self.__checkError(r)

        #Decode 

        if chipType == 5:
            pixelConfigs = np.zeros((256, 256),
                                    dtype=[('maskBit', np.int16), ('testBit', np.int16), ('thlAdj', np.int16),
                                           ('thhAdj', np.int16)])
            for i in range(256):
                for j in range(256):
                    tmp = bin(data[i * 256 + j])  #[2:].rjust(16, '0')
                    pixelConfigs[i, j]['maskBit'] = int(tmp[17], 2)
                    pixelConfigs[i, j]['testBit'] = int(tmp[16], 2)
                    pixelConfigs[i, j]['thlAdj'] = int(tmp[10:15], 2)
                    pixelConfigs[i, j]['thhAdj'] = int(tmp[5:10], 2)

        else:
            pixelConfigs = np.zeros((256, 256),
                                    dtype=[('maskBit', np.int16), ('testBit', np.int16), ('thlAdj', np.int16),
                                           ('mode', np.int16)])
            for i in range(256):
                for j in range(256):
                    tmp = bin(data[i * 256 + j])[2:].rjust(8, '0')
                    pixelConfigs[i, j]['maskBit'] = int(tmp[7], 2)
                    pixelConfigs[i, j]['testBit'] = int(tmp[6], 2)
                    pixelConfigs[i, j]['thlAdj'] = int(tmp[2:6], 2)
                    pixelConfigs[i, j]['mode'] = int(tmp[0:2], 2)
        return pixelConfigs

    def mpxCtrlSetPixelsCfg(self, devID, pixCfg):
        """
        Sets the pixel configuration of a Timepix chip 
        """
        size = c_int(65536)  #use pix count?
        chipNumber = c_int(0)  #use from info
        data = np.ndarray([65536], c_ubyte)
        x = cast(data.ctypes.data, POINTER(c_byte))

        #Convert to byte 
        for i in range(256):
            for j in range(256):
                mode = bin(pixCfg[i, j]['mode'])[2:].rjust(2, '0')
                thlAdj = bin(pixCfg[i, j]['thlAdj'])[2:].rjust(4, '0')
                testBit = bin(pixCfg[i, j]['testBit'])[2:]
                maskBit = bin(pixCfg[i, j]['maskBit'])[2:]
                tmp = mode + thlAdj + testBit + maskBit

                if len(tmp) != 8:
                    print 'byte length has to be 8, is now', len(tmp)

                data[i * 256 + j] = int(tmp, 2)
        r = self.mgr.mpxCtrlSetPixelsCfg(devID, x, size, chipNumber)
        self.__checkError(r)
        return r