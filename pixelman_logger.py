from cernthon.helpers.moduleslib import networked_function

logfile = None
file_name = None

@networked_function(buffered=False)
def save_file(filename):
    global logfile, file_name
    file_name = filename
    logfile = open(filename, 'w')


@networked_function(buffered=False)
def write(event):
    global logfile
    logfile.write(event)
    logfile.flush()
    logfile.close()
    fd = open(file_name)
    h2 = hash(''.join(fd.readlines()))
    fd.close()
    return h2


@networked_function(buffered=False)
def ececute_something(func, *args, **kwargs):
    ret = func(*args, **kwargs)
    return ret