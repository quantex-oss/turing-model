# TODO Fix this

import numpy as np
from numba import njit, float64

from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.utilities.error import TuringError

from turing_models.models.model_black_scholes_analytical import bs_value

###############################################################################
# Analytical Black Scholes model implementation and approximations
###############################################################################


@njit(float64[:](float64, float64, float64, float64, float64[:],
                 float64[:]), cache=True)
def optionImpliedDbn(s, t, r, q, strikes, sigmas):
    ''' This function calculates the option smile/skew-implied probability
    density function times the interval width. '''

    if len(strikes) != len(sigmas):
        raise TuringError("Strike and Sigma vector do not have same length.")

    numSteps = len(strikes)

    sigma = sigmas[0]
    strike = strikes[0]

    sigma = sigmas[1]
    strike = strikes[1]

    inflator = np.exp((r-0) * t)
    dK = strikes[1] - strikes[0]
    values = np.zeros(numSteps)

    for ik in range(0, numSteps):
        strike = strikes[ik]
        sigma = sigmas[ik]
        v = bs_value(s, t, strike, r, q, sigma,
                     TuringOptionTypes.EUROPEAN_CALL.value, False)
        values[ik] = v

    # Calculate the density rho(K) dK
    densitydk = np.zeros(numSteps)

    for ik in range(1, numSteps-1):
        d2VdK2 = (values[ik+1] - 2.0 * values[ik] + values[ik-1]) / dK

 #       print("%d %12.8f %12.8f %12.8f" %
 #             (ik, strikes[ik], values[ik], d2VdK2))

        densitydk[ik] = d2VdK2 * inflator

    return densitydk

###############################################################################
