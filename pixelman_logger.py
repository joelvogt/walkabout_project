from walkabout.helpers.moduleslib import networked_function

logfile = None
file_name = None
import numpy as np

@networked_function(buffered=False)
def save_file(filename):
    global logfile, file_name
    file_name = filename
    logfile = open(filename, 'w')


@networked_function(buffered=False)
def write(event):
    global logfile
    print('event')
    logfile.write(event)
    logfile.flush()
    logfile.close()
    # fd = open(file_name)
    # h2 = hash(''.join(fd.readlines()))
    # fd.close()
    # return h2


@networked_function(buffered=True)
def do_something(func, *args, **kwargs):
    print(type(func))


@networked_function(buffered=False)
def get_sum(arr):
    return np.sum(arr)
