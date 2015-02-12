import os

from walkabout.helpers.moduleslib import networked_function


logfile = None


@networked_function(buffered=False)
def save_file(filename):
    global logfile
    if r'/' in filename:
        path = filename.split('/')
    elif r'\\' in filename:
        path = filename.split('\\')
    else:
        path = [filename]
    current_dir = []
    for directory in path[:-1]:
        current_dir.append(directory)
        if not os.path.exists(directory):
            os.mkdir(os.path.join(current_dir))
    logfile = open(filename, 'w')


@networked_function(buffered=True)
def write(event):
    global logfile
    logfile.write(event)
    logfile.flush()
