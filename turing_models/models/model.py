import numpy as np
from numba import jit, njit, float64, int64
from turing_models.utilities.mathematics import cholesky

###############################################################################

class TuringModel():
    
    def __init__(implementationType,
                 parameterDict: dict):
 
        self._implementationType = implementationType
        self._parameterDist = parameterDict

###############################################################################
