# TODO Fix this

import numpy as np
from scipy.stats import norm

from turing_models.utilities.helper_functions import to_string
from turing_models.utilities.global_types import TuringOptionTypes

from turing_models.utilities.mathematics import N

###############################################################################
# NOTE: Keeping this separate from SABR for the moment.
###############################################################################


class TuringModelBlackShifted():
    ''' Black's Model which prices call and put options in the forward
    measure according to the Black-Scholes equation. This model also allows
    the distribution to be shifted to the negative in order to allow for
    negative interest rates. '''

    def __init__(self, volatility, shift, implementation=0):
        ''' Create TuringModel black using parameters. '''
        self._volatility = volatility
        self._shift = shift
        self._implementation = 0
        self._numSteps = 0
        self._seed = 0
        self._param1 = 0
        self._param2 = 0

###############################################################################

    def value(self,
              forwardRate,   # Forward rate
              strikeRate,    # Strike Rate
              timeToExpiry,  # time to expiry in years
              df,            # Discount Factor to expiry date
              callOrPut):    # Call or put
        ''' Price a derivative using Black's model which values in the forward
        measure following a change of measure. The sign of the shift is the
        same as Matlab. '''

        s = self._shift
        f = forwardRate
        t = timeToExpiry
        k = strikeRate
        sqrtT = np.sqrt(t)
        vol = self._volatility

        d1 = np.log((f+s)/(k+s)) + vol * vol * t / 2
        d1 = d1 / (vol * sqrtT)
        d2 = d1 - vol * sqrtT

        if callOrPut == TuringOptionTypes.EUROPEAN_CALL:
            return df * ((f+s) * N(d1) - (k+s) * N(d2))
        elif callOrPut == TuringOptionTypes.EUROPEAN_PUT:
            return df * ((k+s) * N(-d2) - (f+s) * N(-d1))
        else:
            raise Exception("Option type must be a European Call(C) or Put(P)")

###############################################################################

    def __repr__(self):
        s = to_string("OBJECT TYPE", type(self).__name__)
        s += to_string("VOLATILITY", self._volatility)
        s += to_string("SHIFT", self._shift)
        s += to_string("IMPLEMENTATION", self._implementation)
        s += to_string("NUMSTEPS", self._numSteps)
        return s

###############################################################################
