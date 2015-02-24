import numpy as np

from walkabout.adapters.numpy_adapters import numpy_to_jython
from walkabout.helpers.moduleslib import networked_function


@networked_function(buffered=True)
def b_doSum(arr):
    return numpy_to_jython(np.sum(map(lambda x: x ** 2, arr)))


@networked_function(buffered=False)
def doSum(arr):
    return numpy_to_jython(np.sum(map(lambda x: x ** 2, arr)))