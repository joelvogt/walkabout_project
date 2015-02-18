import numpy as np

from walkabout.helpers.moduleslib import networked_function
from walkabout.adapters.numpy_adapters import numpy_to_jython

@networked_function(buffered=True)
@numpy_to_jython
def b_doSum(arr):
    return np.sum(arr)


@networked_function(buffered=False)
@numpy_to_jython
def doSum(arr):
    return np.sum(arr)