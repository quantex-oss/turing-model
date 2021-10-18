import numpy as np
from turing_models.utilities.error import TuringError


class TuringDistribution():
    ''' Container class for a probability density function. ''' 
    
    def __init__(self, x, y):
        ''' Initialise TuringDistribution with x values and associated vector of
        density times dx values. '''

        if len(x) != len(y):
            raise TuringError("Length of x and y not the same")

        self._x = np.array(x)
        self._densitydx = np.array(y)

    def sum(self):        
        ''' This should equal 1.0 for the entire distribution. '''
        return np.sum(self._densitydx)

###############################################################################
