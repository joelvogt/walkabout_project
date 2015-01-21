#-*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import time, sys, functools, cPickle, tempfile


MESSAGE_HEADER = 'HDR'
MESSAGE_HEADER_END = 'EOH' 
HEADER_DELIMITER = '|'
DEFAULT_BUFFER_SIZE = 16384

class AbstractIterator(object):

    def __init__(self, values):
        self._values = values


def string_to_int(value): return int(value) if '.' not in value and ord(value[0]) >= ord('0') and ord(value[0]) <= ord('9') else value


def slice_evenly(arr,slice_size):
    for i in xrange(0,len(arr),slice_size):
        yield arr[i:i+slice_size]


def __serialize_data_config():
    python_interpreters = dict(
        Jython = cPickle.dumps,
        CPython = functools.partial(cPickle.dumps, protocol=2),
        PyPy = functools.partial(cPickle.dumps, protocol=2)
    )
    return python_interpreters[sys.subversion[0]]


def __deserialize_data_config():
    return cPickle.loads


serialize_data = __serialize_data_config()


deserialize_data = __deserialize_data_config()


class InputStreamBuffer(object):
    def __init__(self, data=None, buffer_size=DEFAULT_BUFFER_SIZE):
        self._buffer_size = buffer_size
        self._in_memory = [0, buffer_size]
        self._fd = tempfile.TemporaryFile()
        self._in_disk = [0, 0]
        self._size = 0
        if data:
            self.extend(data)

    def __del__(self):
        self._fd.close()
        # os.remove(self._temp_file)

    def __adjust_memory_pointers(self, i):
        if i >= 0:
            return self._in_disk[0] + i
        else:
            return self._size + i

    def extend(self, data):
        self._fd.seek(self._in_disk[0] + self._size)
        self._fd.write(data)
        self._fd.flush()

        self._size += len(data)

    def __getitem__(self, i):
        self._fd.seek(self.__adjust_memory_pointers(i))
        return self._fd.read(1)

    def trim(self, position):
        self._size -= abs(position)
        # self.data = self.data[position:] if position >= 0 else self.data[:position]
        if position >= 0:
            self._in_disk[0] += position

    def __getslice__(self, i, j):
        i = self.__adjust_memory_pointers(i)
        j = self.__adjust_memory_pointers(j)
        slice = j - i
        self._fd.seek(i)
        return self._fd.read(slice)
