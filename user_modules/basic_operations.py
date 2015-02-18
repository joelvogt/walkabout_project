import numpy as np

from walkabout.helpers.moduleslib import networked_function
from walkabout.adapters.numpy_adapters import numpy_to_jython


@networked_function(buffered=True)
def b_doSum(arr):
    return numpy_to_jython(np.sum(arr))


@networked_function(buffered=False)
def doSum(arr):
    return numpy_to_jython(np.sum(arr))