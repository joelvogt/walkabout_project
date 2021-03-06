# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'

import tempfile


def string_to_int(value):
    if '.' not in value and ord('0') <= ord(value[0]) <= ord('9'):
        return int(value)
    else:
        return value


def slice_evenly(arr, slice_size):
    for i in xrange(0, len(arr), slice_size):
        yield arr[i:i + slice_size]


class InputStreamBuffer(object):
    def __init__(self, buffer_size, data=None, file_name=None):
        self._buffer_size = buffer_size
        self._in_memory = [0, self._buffer_size]
        if file_name is not None:
            self.fd = open(file_name, 'w')
        else:
            self.fd = tempfile.SpooledTemporaryFile(bufsize=self._buffer_size)
        self._in_disk = [0, 0]
        self.size = 0
        if data:
            self.extend(data)

    def __del__(self):
        self.fd.close()

    def __adjust_memory_pointers(self, i):
        if i >= 0:
            return self._in_disk[0] + i
        else:
            return self.size + i

    def extend(self, data):
        self.fd.seek(self._in_disk[0] + self.size)

        self.fd.write(data)
        self.fd.flush()

        self.size += len(data)

    def __getitem__(self, i):
        self.fd.seek(self.__adjust_memory_pointers(i))
        return self.fd.read(1)

    def trim(self, position):
        self.size -= abs(position)
        # self.data = self.data[position:] if position >= 0 else self.data[:position]
        if position >= 0:
            self._in_disk[0] += position

    def __getslice__(self, i, j):
        i = self.__adjust_memory_pointers(i)
        j = self.__adjust_memory_pointers(j)
        file_slice = j - i
        self.fd.seek(i)
        return self.fd.read(file_slice)
