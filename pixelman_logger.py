
from helpers.moduleslib import networked_function
from helpers.datalib import InputStreamBuffer

logfile=None

@networked_function(buffered=False)
def open(filename):
    global logfile
    logfile = InputStreamBuffer(file_name=filename)


@networked_function(buffered=True)
def write(event):
    global logfile
    logfile.extend(event)
