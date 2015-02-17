import numpy as np

from walkabout.helpers.moduleslib import networked_function


@networked_function(buffered=True)
def b_doSum(arr):
    return np.sum(arr)


@networked_function(buffered=False)
def doSum(arr):
    return np.sum(arr)