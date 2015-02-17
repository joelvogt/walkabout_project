import numpy as np

from walkabout.helpers.moduleslib import networked_function


@networked_function(buffered=True)
def doSum(arr):
    return np.sum(arr)