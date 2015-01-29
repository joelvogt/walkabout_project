# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import sys
import functools
import cPickle
import tempfile
import zlib


MESSAGE_HEADER = 'HDR'
MESSAGE_HEADER_END = 'EOH'
HEADER_DELIMITER = '|'
NETWORK_BUFFER_SIZE = 8192


def string_to_int(value): return int(value) if '.' not in value and ord('0') <= ord(value[0]) <= ord(
    '9') else value


def slice_evenly(arr, slice_size):
    for i in xrange(0, len(arr), slice_size):
        yield arr[i:i + slice_size]


def __serialize_data_config():
    def compress(func):
        def on_call(data):
            return zlib.compress(func(data))

        return on_call

    python_interpreters = dict(
        Jython=cPickle.dumps,
        CPython=functools.partial(cPickle.dumps, protocol=2),
        PyPy=functools.partial(cPickle.dumps, protocol=2)
    )
    return python_interpreters[sys.subversion[0]]


def decompress(func):
    def on_call(data):
        return func(zlib.decompress(data))

    return on_call


def __deserialize_data_config():
    return cPickle.loads


serialize_data = __serialize_data_config()

deserialize_data = __deserialize_data_config()


class InputStreamBuffer(object):
    def __init__(self, data=None, file_name=None):
        self._buffer_size = NETWORK_BUFFER_SIZE
        self._in_memory = [0, self._buffer_size]
        if file_name is not None:
            self._fd = open(file_name, 'w')
        else:
            self._fd = tempfile.SpooledTemporaryFile(bufsize=self._buffer_size)
        self._in_disk = [0, 0]
        self.size = 0
        if data:
            self.extend(data)

    def __del__(self):
        self._fd.close()

    def __adjust_memory_pointers(self, i):
        if i >= 0:
            return self._in_disk[0] + i
        else:
            return self.size + i

    def extend(self, data):
        self._fd.seek(self._in_disk[0] + self.size)

        self._fd.write(data)
        self._fd.flush()

        self.size += len(data)

    def __getitem__(self, i):
        self._fd.seek(self.__adjust_memory_pointers(i))
        return self._fd.read(1)

    def trim(self, position):
        self.size -= abs(position)
        # self.data = self.data[position:] if position >= 0 else self.data[:position]
        if position >= 0:
            self._in_disk[0] += position

    def __getslice__(self, i, j):
        i = self.__adjust_memory_pointers(i)
        j = self.__adjust_memory_pointers(j)
        file_slice = j - i
        self._fd.seek(i)
        return self._fd.read(file_slice)
