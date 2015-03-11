from time import time




# remote_file.save_file('logfile.txt')
range_value = 100

from user_modules.basic_operations import doSum

start = time()

out = []
for i in xrange(10):
    out.append(doSum(range(range_value)))
print(len(out))
stop = time()
print("local %f" % (stop - start))
from walkabout.base.client import import_module


remote_file = import_module('basic_operations')
start = time()
print('stsat')
for i in xrange(10):
    remote_file.b_doSum(range(range_value))
print(len(list(remote_file.b_doSum)))
stop = time()
print("remote buffered %f" % (stop - start))


start = time()

out = []
for i in xrange(10):
    out.append(remote_file.doSum(range(range_value)))
print(len(out))
stop = time()
print("remote unbuffered %f" % (stop - start))

print('end')