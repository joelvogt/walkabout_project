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

