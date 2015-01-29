from cernthon.helpers.moduleslib import networked_function

logfile = None


@networked_function(buffered=False)
def save_file(filename):
    global logfile
    logfile = open(filename, 'w')


@networked_function(buffered=False)
def write(event):
    global logfile
    logfile.write(event)
    logfile.flush()
    logfile.close()
    fd = open(logfile)
    h2 = hash(''.join(fd.readlines()))
    fd.close()
    return h2


@networked_function(buffered=False)
def foo():
    return 'bar'