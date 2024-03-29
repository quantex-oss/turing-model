import numpy as np

from turing_models.utilities.error import TuringError
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_variables import gDaysInYear

##########################################################################
# TODO: Market calibration (fitting)
##########################################################################


class TuringIborCapVolCurveFn():
    ''' Class to manage a term structure of caplet volatilities using the
    parametric form suggested by Rebonato (1999). '''

    def __init__(self,
                 curveDate,
                 a,
                 b,
                 c,
                 d):

        self._curveDate = curveDate
        self._a = a
        self._b = b
        self._c = c
        self._d = d

###############################################################################

    def capFloorletVol(self, dt):
        ''' Return the caplet volatility. '''

        if isinstance(dt, TuringDate):
            t = (dt - self._curveDate) / gDaysInYear
            vol = (self._a + self._b*t) * np.exp(-self._c*t) + self._d

        if vol < 0.0:
            raise TuringError("Negative volatility. Not permitted.")

        return vol

###############################################################################
