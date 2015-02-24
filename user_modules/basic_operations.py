import numpy as np

from walkabout.adapters.numpy_adapters import numpy_to_jython
from walkabout.helpers.moduleslib import networked_function


@networked_function(buffered=True)
def b_doSum(arr):
    length = len(arr)
    values = map(lambda x: x ** 2, arr)
    return numpy_to_jython(np.sum(values[length / 2:]))


@networked_function(buffered=False)
def doSum(arr):
    length = len(arr)
    values = map(lambda x: x ** 2, arr)
    return numpy_to_jython(np.sum(values[length / 2:]))