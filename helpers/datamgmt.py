#-*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
import time, sys, functools, cPickle, os, tempfile


MESSAGE_HEADER = 'HDR'
HEADER_DELIMITER = '||'

class AbstractIterator(object):

    def __init__(self, values):
        self._values = values


def string_to_int(value): return int(value) if '.' not in value and ord(value[0]) >= ord('0') and ord(value[0]) <= ord('9') else value

# def encode_stream_with_header(message):
#     message_length = str(len(message))
#     header_length = str(len(message_length))
#     return '%s%s%s' %(header_length, message_length, message)
#
# def decode_stream_with_header(stream):
#     header_length = int(stream[0]) + 1
#     message_length = int(stream[1:header_length])
#     print 'decode'
#     print stream[header_length:message_length]
#     return stream[header_length:message_length], stream[message_length:]


def slice_evenly(arr,slice_size):
    for i in xrange(0,len(arr),slice_size):
        yield arr[i:i+slice_size]


def __serialize_data_config():
    python_interpreters = dict(
        Jython = cPickle.dumps,
        CPython = functools.partial(cPickle.dumps, protocol=0),
        PyPy = functools.partial(cPickle.dumps, protocol=2)
    )
    return python_interpreters[sys.subversion[0]]


def __deserialize_data_config():
    return cPickle.loads


serialize_data = __serialize_data_config()


deserialize_data = __deserialize_data_config()


class InputStreamBuffer(object):
    def __init__(self, data=None, buffer_size=8192):
        self._buffer_size = buffer_size
        # self._temp_file = 'inputbuffer-{0}.tmp'.format(time.clock())
        self._in_memory = [0, buffer_size]
        # self._fd = open(self._temp_file, mode='w+', buffering=buffer_size)
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
        # self._fd.flush()
        # sys.stdout.flush()
        self._fd.seek(self.__adjust_memory_pointers(i))
        return self._fd.read(1)

    def trim(self, position):
        self._size -= abs(position)
        # self.data = self.data[position:] if position >= 0 else self.data[:position]
        if position >= 0:
            self._in_disk[0] += position

    def __getslice__(self, i, j):
        # self._fd.flush()
        # sys.stdout.flush()
        i = self.__adjust_memory_pointers(i)
        j = self.__adjust_memory_pointers(j)
        slice = j - i
        self._fd.seek(i)
        return self._fd.read(slice)





class Timer:
    def __enter__(self):
        self.start = time.clock()
        return self

    def __exit__(self, *args):
        self.end = time.clock()
        self.interval = self.end - self.start