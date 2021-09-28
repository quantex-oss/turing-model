import numpy as np
from scipy.optimize import minimize
import scipy.stats as sci
import math

import matplotlib.pyplot as plt
from numba import njit, float64, int64

from turing_models.utilities.error import TuringError
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.products.fx.fx_vanilla_option import TuringFXVanillaOption
from turing_models.models.model_option_implied_dbn import optionImpliedDbn
from turing_models.products.fx.fx_mkt_conventions import TuringFXATMMethod
from turing_models.products.fx.fx_mkt_conventions import TuringFXDeltaMethod
from turing_models.utilities.helper_functions import checkArgumentTypes, to_string
from turing_models.market.curves.discount_curve import TuringDiscountCurve

from turing_models.models.model_black_scholes import TuringModelBlackScholes

from turing_models.models.model_volatility_fns import volFunctionClark, volFunctionVV
from turing_models.models.model_volatility_fns import volFunctionBloomberg
from turing_models.models.model_volatility_fns import TuringVolFunctionTypes
from turing_models.models.model_sabr import volFunctionSABR
from turing_models.models.model_sabr import volFunctionSABR_BETA_ONE
from turing_models.models.model_sabr import volFunctionSABR_BETA_HALF

from turing_models.utilities.mathematics import norminvcdf

from turing_models.models.model_black_scholes_analytical import bs_value
from turing_models.products.fx.fx_vanilla_option import fastDelta
from turing_models.utilities.distribution import TuringDistribution

from turing_models.utilities.solvers_1d import newton_secant
from turing_models.utilities.solvers_nm import nelder_mead
from turing_models.utilities.global_types import TuringSolverTypes
###############################################################################


@njit(fastmath=True, cache=True)
def _g(K, *args):
    ''' This is the objective function used in the determination of the FX
    option implied strike which is computed in the class below. '''

    s = args[0]
    t = args[1]
    rd = args[2]
    rf = args[3]
    volatility = args[4]
    deltaMethodValue = args[5]
    optionTypeValue = args[6]
    deltaTarget = args[7]

    deltaOut = fastDelta(s, t, K, rd, rf,
                         volatility,
                         deltaMethodValue,
                         optionTypeValue)

    objFn = deltaTarget - deltaOut
    return objFn

###############################################################################


def _solveToHorizon(s, t, rd, rf,
                    bf25DVol, bf10DVol, d25P,
                    d25ATM, d25C, d10P, d10ATM,
                    d10C):

    ###########################################################################
    # Determine strikes of the key points on the curve.
    ###########################################################################

    use10D = True
    use25D = True

    if bf25DVol == -999.0:
        use25D = False

    if bf10DVol == -999.0:
        use10D = False

    if use25D is True:

        Df = np.exp(-np.multiply(rf, t))
        delta = 0.25
        alpha = -sci.norm.ppf(delta * np.reciprocal(Df))
        mu = rd - rf
        F = s * np.exp(np.multiply(mu, t))

        # Strikes
        KATM = np.array([])
        K25DeltaCall = np.array([])
        K25DeltaPut = np.array([])

        K25DeltaPut = np.append(K25DeltaPut, F * math.exp(
            -(alpha * d25P * math.sqrt(t)) + (0.5 * d25P ** 2) * t))
        KATM = np.append(KATM, F * math.exp(0.5 * t * (d25ATM) ** 2))
        K25DeltaCall = np.append(K25DeltaCall, F * math.exp(
            alpha * d25C * math.sqrt(t) + (0.5 * d25C ** 2) * t))

        return K25DeltaPut, KATM, K25DeltaCall

    elif use10D is True:

        Df = np.exp(-np.multiply(rf, t))
        delta = 0.10
        alpha = -sci.norm.ppf(delta * np.reciprocal(Df))
        mu = rd - rf
        F = s * np.exp(np.multiply(mu, t))

        # Strikes
        KATM = np.array([])
        K10DeltaCall = np.array([])
        K10DeltaPut = np.array([])

        K10DeltaPut = np.append(K10DeltaPut, F * math.exp(
            -(alpha * d10P * math.sqrt(t)) + (0.5 * d10P ** 2) * t))
        KATM = np.append(KATM, F * math.exp(0.5 * t * (d10ATM) ** 2))
        K10DeltaCall = np.append(K10DeltaCall, F * math.exp(
            alpha * d10C * math.sqrt(t) + (0.5 * d10C ** 2) * t))

        return K10DeltaPut, KATM, K10DeltaCall


###############################################################################


@njit(float64(float64[:], float64, float64, float64), cache=True, fastmath=True)
def volFunction(params, f, k, t):
    ''' Return the volatility for a strike using vanna-volga method. '''

#    print("volFunction", volFunctionTypeValue)
    vol = volFunctionVV(params, f, k, t)
    return vol

###############################################################################


@njit(cache=True, fastmath=True)
def _deltaFit(k, *args):
    ''' This is the objective function used in the determination of the FX
    Option implied strike which is computed in the class below. I map it into
    inverse normcdf space to avoid the flat slope of this function at low vol
    and high K. It speeds up the code as it allows initial values close to
    the solution to be used. '''

    s = args[0]
    t = args[1]
    rd = args[2]
    rf = args[3]
    optionTypeValue = args[4]
    deltaTypeValue = args[5]
    inverseDeltaTarget = args[6]
    params = args[7]

    f = s * np.exp((rd-rf)*t)
    v = volFunction(params, f, k, t)
    deltaOut = fastDelta(s, t, k, rd, rf, v, deltaTypeValue, optionTypeValue)
    inverseDeltaOut = norminvcdf(np.abs(deltaOut))
    invObjFn = inverseDeltaTarget - inverseDeltaOut

#    print(k, f, v, deltaOut, invObjFn)

    return invObjFn

###############################################################################
# Unable to cache this function due to dynamic globals warning. Revisit.
###############################################################################


@njit(float64(float64, float64, float64, float64, int64, float64,
              int64, float64, float64[:]),
      fastmath=True)
def _solveForSmileStrike(s, t, rd, rf,
                         optionTypeValue,
                         deltaTarget,
                         deltaMethodValue,
                         initialGuess,
                         parameters
                         ):
    ''' Solve for the strike that sets the delta of the option equal to the
    target value of delta allowing the volatility to be a function of the
    strike. '''

    inverseDeltaTarget = norminvcdf(np.abs(deltaTarget))

    argtuple = (s, t, rd, rf,
                optionTypeValue, deltaMethodValue,
                inverseDeltaTarget,
                parameters)

    K = newton_secant(_deltaFit, x0=initialGuess, args=argtuple,
                      tol=1e-8, maxiter=50)

    return K

###############################################################################
# Unable to cache function and if I remove njit it complains about pickle
###############################################################################


@njit(float64(float64, float64, float64, float64, int64, float64,
              int64, float64), fastmath=True)
def solveForStrike(spotFXRate,
                   tdel, rd, rf,
                   optionTypeValue,
                   deltaTarget,
                   deltaMethodValue,
                   volatility):
    ''' This function determines the implied strike of an FX option
    given a delta and the other option details. It uses a one-dimensional
    Newton root search algorith to determine the strike that matches an
    input volatility. '''

    # =========================================================================
    # IMPORTANT NOTE:
    # =========================================================================
    # For some delta quotation conventions I can solve for K explicitly.
    # Note that as I am using the function norminvdelta to calculate the
    # inverse value of delta, this may not, on a round trip using N(x), give
    # back the value x as it is calculated to a different number of decimal
    # places. It should however agree to 6-7 decimal places. Which is OK.
    # =========================================================================

    if deltaMethodValue == TuringFXDeltaMethod.SPOT_DELTA.value:

        domDF = np.exp(-rd*tdel)
        forDF = np.exp(-rf*tdel)

        if optionTypeValue == TuringOptionTypes.EUROPEAN_CALL.value:
            phi = +1.0
        else:
            phi = -1.0

        F0T = spotFXRate * forDF / domDF
        vsqrtt = volatility * np.sqrt(tdel)
        arg = deltaTarget*phi/forDF  # CHECK THIS !!!
        norminvdelta = norminvcdf(arg)
        K = F0T * np.exp(-vsqrtt * (phi * norminvdelta - vsqrtt/2.0))
        return K

    elif deltaMethodValue == TuringFXDeltaMethod.FORWARD_DELTA.value:

        domDF = np.exp(-rd*tdel)
        forDF = np.exp(-rf*tdel)

        if optionTypeValue == TuringOptionTypes.EUROPEAN_CALL.value:
            phi = +1.0
        else:
            phi = -1.0

        F0T = spotFXRate * forDF / domDF
        vsqrtt = volatility * np.sqrt(tdel)
        arg = deltaTarget*phi
        norminvdelta = norminvcdf(arg)
        K = F0T * np.exp(-vsqrtt * (phi * norminvdelta - vsqrtt/2.0))
        return K

    elif deltaMethodValue == TuringFXDeltaMethod.SPOT_DELTA_PREM_ADJ.value:

        argtuple = (spotFXRate, tdel, rd, rf, volatility,
                    deltaMethodValue, optionTypeValue, deltaTarget)

        K = newton_secant(_g, x0=spotFXRate, args=argtuple,
                          tol=1e-7, maxiter=50)

        return K

    elif deltaMethodValue == TuringFXDeltaMethod.FORWARD_DELTA_PREM_ADJ.value:

        argtuple = (spotFXRate, tdel, rd, rf, volatility,
                    deltaMethodValue, optionTypeValue, deltaTarget)

        K = newton_secant(_g, x0=spotFXRate, args=argtuple,
                          tol=1e-7, maxiter=50)

        return K

    else:

        raise TuringError("Unknown TuringFXDeltaMethod")

###############################################################################


class TuringFXVolSurfaceVV:
    ''' Class to perform a calibration of a chosen parametrised surface to the
    prices of FX options at different strikes and expiry tenors. Thes
    calibration inputs are the ATM and 25 and 10 Delta volatilities in terms of
    the market strangle amd risk reversals. Volatility function is Vanna_Volga.
    Visualising the volatility curve is useful. Also, there is no guarantee
    that the implied pdf will be positive.'''

    def __init__(self,
                 valueDate: TuringDate,
                 spotFXRate: float,
                 currencyPair: str,
                 domDiscountCurve: TuringDiscountCurve,
                 forDiscountCurve: TuringDiscountCurve,
                 tenors: (list),
                 atmVols: (list, np.ndarray),
                 butterfly25DeltaVols: (list, np.ndarray),
                 riskReversal25DeltaVols: (list, np.ndarray),
                 butterfly10DeltaVols: (list, np.ndarray),
                 riskReversal10DeltaVols: (list, np.ndarray),
                 alpha: float = 1,
                 atmMethod: TuringFXATMMethod = TuringFXATMMethod.FWD_DELTA_NEUTRAL,
                 deltaMethod: TuringFXDeltaMethod = TuringFXDeltaMethod.SPOT_DELTA,
                 volatilityFunctionType: TuringVolFunctionTypes = TuringVolFunctionTypes.VANNA_VOLGA,
                 finSolverType: TuringSolverTypes = TuringSolverTypes.NELDER_MEAD,
                 tol: float = 1e-8):
        ''' Create the TuringFXVolSurfacePlus object by passing in market vol data
        for ATM, 25 Delta and 10 Delta strikes. The alpha shifts the
        fitting between 25D and 10D. Alpha = 1.0 is 100% 25D while alpha = 0.0
        is 100% 10D. '''

        # I want to allow Nones for some of the market inputs
        if butterfly10DeltaVols is None:
            butterfly10DeltaVols = []

        if riskReversal10DeltaVols is None:
            riskReversal10DeltaVols = []

        if butterfly25DeltaVols is None:
            butterfly25DeltaVols = []

        if riskReversal25DeltaVols is None:
            riskReversal25DeltaVols = []

        checkArgumentTypes(self.__init__, locals())

        self._valueDate = valueDate
        self._spotFXRate = spotFXRate
        self._currencyPair = currencyPair

        if len(currencyPair) != 7:
            raise TuringError("Currency pair must be in ***/***format.")

        self._forName = self._currencyPair[0:3]
        self._domName = self._currencyPair[4:7]

        self._domDiscountCurve = domDiscountCurve
        self._forDiscountCurve = forDiscountCurve
        self._numVolCurves = len(tenors)
        self._tenors = tenors

        if len(atmVols) != self._numVolCurves:
            raise TuringError("Number ATM vols must equal number of tenors")

        self._atmVols = np.array(atmVols)

        self._useMS25DVol = True
        self._useRR25DVol = True
        self._useMS10DVol = True
        self._useRR10DVol = True

        # Some of these can be missing which is signified by length zero
        n = len(butterfly25DeltaVols)

        if n != self._numVolCurves and n != 0:
            raise TuringError("Number MS25D vols must equal number of tenors")

        if n == 0:
            self._useMS25DVol = False

        n = len(riskReversal25DeltaVols)

        if n != self._numVolCurves and n != 0:
            raise TuringError("Number RR25D vols must equal number of tenors")

        if n == 0:
            self._useRR25DVol = False

        n = len(butterfly10DeltaVols)

        if n != self._numVolCurves and n != 0:
            raise TuringError("Number MS10D vols must equal number of tenors")

        if n == 0:
            self._useMS10DVol = False

        n = len(riskReversal10DeltaVols)

        if n != self._numVolCurves and n != 0:
            raise TuringError("Number RR10D vols must equal number of tenors")

        if n == 0:
            self._useRR10DVol = False

        if self._useMS10DVol != self._useRR10DVol:
            raise TuringError(
                "You must provide both 10D RR + 10D MS or neither")

        if self._useMS25DVol != self._useRR25DVol:
            raise TuringError(
                "You must provide both 25D RR + 25D MS or neither")

        if self._useMS10DVol is False and self._useMS25DVol is False:
            raise TuringError(
                "No MS and RR. You must provide 10D or 25D MS + RR.")

        self._butterfly25DeltaVols = np.array(butterfly25DeltaVols)
        self._riskReversal25DeltaVols = np.array(riskReversal25DeltaVols)
        self._butterfly10DeltaVols = np.array(butterfly10DeltaVols)
        self._riskReversal10DeltaVols = np.array(riskReversal10DeltaVols)

        if alpha < 0.0 or alpha > 1.0:
            raise TuringError("Alpha must be between 0.0 and 1.0")

        self._alpha = alpha

        self._atmMethod = atmMethod
        self._deltaMethod = deltaMethod

        if self._deltaMethod == TuringFXDeltaMethod.SPOT_DELTA:
            self._deltaMethodString = "pips_spot_delta"
        elif self._deltaMethod == TuringFXDeltaMethod.FORWARD_DELTA:
            self._deltaMethodString = "pips_fwd_delta"
        elif self._deltaMethod == TuringFXDeltaMethod.SPOT_DELTA_PREM_ADJ:
            self._deltaMethodString = "pct_spot_delta_prem_adj"
        elif self._deltaMethod == TuringFXDeltaMethod.FORWARD_DELTA_PREM_ADJ:
            self._deltaMethodString = "pct_fwd_delta_prem_adj"
        else:
            raise TuringError("Unknown Delta Type")

        self._volatilityFunctionType = volatilityFunctionType
        self._tenorIndex = 0

        self._expiryDates = []

        if isinstance(tenors[0], str):
            for i in range(0, self._numVolCurves):
                expiryDate = valueDate.addTenor(tenors[i])
                self._expiryDates.append(expiryDate)
        else:
            for i in range(0, self._numVolCurves):
                expiryDate = valueDate.addYears(tenors[i])
                self._expiryDates.append(expiryDate)

        self._buildVolSurface(finSolverType=finSolverType, tol=tol)
###############################################################################

    def volatilityFromStrikeDate(self, K, expiryDate):
        ''' Interpolates the Black-Scholes volatility from the volatility
        surface given call option strike and expiry date. Linear interpolation
        is done in variance space. The smile strikes at bracketed dates are
        determined by determining the strike that reproduces the provided delta
        value. This uses the calibration delta convention, but it can be
        overriden by a provided delta convention. The resulting volatilities
        are then determined for each bracketing expiry time and linear
        interpolation is done in variance space and then converted back to a
        lognormal volatility.'''

        texp = (expiryDate - self._valueDate) / gDaysInYear

        volTypeValue = self._volatilityFunctionType.value

        index0 = 0  # lower index in bracket
        index1 = 0  # upper index in bracket

        numCurves = self._numVolCurves

        if numCurves == 1:

            index0 = 0
            index1 = 0

        # If the time is below first time then assume a flat vol
        elif texp <= self._texp[0]:

            index0 = 0
            index1 = 0

        # If the time is beyond the last time then extrapolate with a flat vol
        elif texp >= self._texp[-1]:

            index0 = len(self._texp) - 1
            index1 = len(self._texp) - 1

        else:  # Otherwise we look for bracketing times and interpolate

            for i in range(1, numCurves):

                if texp <= self._texp[i] and texp > self._texp[i-1]:
                    index0 = i-1
                    index1 = i
                    break

        fwd0 = self._F0T[index0]
        fwd1 = self._F0T[index1]

        t0 = self._texp[index0]
        t1 = self._texp[index1]

        vol0 = volFunction(self._parameters[index0],
                           fwd0, K, t0)

        if index1 != index0:

            vol1 = volFunction(self._parameters[index1],
                               fwd1, K, t1)

        else:

            vol1 = vol0

        # In the expiry time dimension, both volatilities are interpolated
        # at the same strikes but different deltas.
        vart0 = vol0*vol0*t0
        vart1 = vol1*vol1*t1

        if np.abs(t1-t0) > 1e-6:
            vart = ((texp-t0) * vart1 + (t1-texp) * vart0) / (t1 - t0)

            if vart < 0.0:
                raise TuringError("Negative variance.")

            volt = np.sqrt(vart/texp)

        else:
            volt = vol1

        return volt

###############################################################################

    def deltaToStrike(self, callDelta, expiryDate, deltaMethod=None):
        ''' Interpolates the strike at a delta and expiry date. Linear
        interpolation is used in strike.'''

        texp = (expiryDate - self._valueDate) / gDaysInYear

        s = self._spotFXRate

        if deltaMethod is None:
            deltaMethodValue = self._deltaMethod.value
        else:
            deltaMethodValue = deltaMethod.value

        index0 = 0  # lower index in bracket
        index1 = 0  # upper index in bracket

        numCurves = self._numVolCurves

        # If there is only one time horizon then assume flat vol to this time
        if numCurves == 1:

            index0 = 0
            index1 = 0

        # If the time is below first time then assume a flat vol
        elif texp <= self._texp[0]:

            index0 = 0
            index1 = 0

        # If the time is beyond the last time then extrapolate with a flat vol
        elif texp > self._texp[-1]:

            index0 = len(self._texp) - 1
            index1 = len(self._texp) - 1

        else:  # Otherwise we look for bracketing times and interpolate

            for i in range(1, numCurves):

                if texp <= self._texp[i] and texp > self._texp[i-1]:
                    index0 = i-1
                    index1 = i
                    break

        #######################################################################

        t0 = self._texp[index0]
        t1 = self._texp[index1]

        initialGuess = self._K_ATM[index0]

        K0 = _solveForSmileStrike(s, texp, self._rd[index0], self._rf[index0],
                                  TuringOptionTypes.EUROPEAN_CALL.value,
                                  callDelta,
                                  deltaMethodValue,
                                  initialGuess,
                                  self._parameters[index0])

        if index1 != index0:

            K1 = _solveForSmileStrike(s, texp,
                                      self._rd[index1],
                                      self._rf[index1],
                                      TuringOptionTypes.EUROPEAN_CALL.value,
                                      callDelta,
                                      deltaMethodValue,
                                      initialGuess,
                                      self._parameters[index1])
        else:

            K1 = K0

        # In the expiry time dimension, both volatilities are interpolated
        # at the same strikes but different deltas.

        if np.abs(t1-t0) > 1e-6:

            K = ((texp-t0) * K1 + (t1-texp) * K0) / (K1 - K0)

        else:

            K = K1

        return K

###############################################################################

    def volatilityFromDeltaDate(self, callDelta, expiryDate,
                                deltaMethod=None):
        ''' Interpolates the Black-Scholes volatility from the volatility
        surface given a call option delta and expiry date. Linear interpolation
        is done in variance space. The smile strikes at bracketed dates are
        determined by determining the strike that reproduces the provided delta
        value. This uses the calibration delta convention, but it can be
        overriden by a provided delta convention. The resulting volatilities
        are then determined for each bracketing expiry time and linear
        interpolation is done in variance space and then converted back to a
        lognormal volatility.'''

        texp = (expiryDate - self._valueDate) / gDaysInYear

        volTypeValue = self._volatilityFunctionType.value

        s = self._spotFXRate

        if deltaMethod is None:
            deltaMethodValue = self._deltaMethod.value
        else:
            deltaMethodValue = deltaMethod.value

        index0 = 0  # lower index in bracket
        index1 = 0  # upper index in bracket

        numCurves = self._numVolCurves

        # If there is only one time horizon then assume flat vol to this time
        if numCurves == 1:

            index0 = 0
            index1 = 0

        # If the time is below first time then assume a flat vol
        elif texp <= self._texp[0]:

            index0 = 0
            index1 = 0

        # If the time is beyond the last time then extrapolate with a flat vol
        elif texp > self._texp[-1]:

            index0 = len(self._texp) - 1
            index1 = len(self._texp) - 1

        else:  # Otherwise we look for bracketing times and interpolate

            for i in range(1, numCurves):

                if texp <= self._texp[i] and texp > self._texp[i-1]:
                    index0 = i-1
                    index1 = i
                    break

        fwd0 = self._F0T[index0]
        fwd1 = self._F0T[index1]

        t0 = self._texp[index0]
        t1 = self._texp[index1]

        initialGuess = self._K_ATM[index0]

        K0 = _solveForSmileStrike(s, texp, self._rd[index0], self._rf[index0],
                                  TuringOptionTypes.EUROPEAN_CALL.value,
                                  callDelta,
                                  deltaMethodValue,
                                  initialGuess,
                                  self._parameters[index0])

        vol0 = volFunction(self._parameters[index0],
                           fwd0, K0, t0)

        if index1 != index0:

            K1 = _solveForSmileStrike(s, texp,
                                      self._rd[index1],
                                      self._rf[index1],
                                      TuringOptionTypes.EUROPEAN_CALL.value,
                                      callDelta,
                                      deltaMethodValue,
                                      initialGuess,
                                      self._parameters[index1])

            vol1 = volFunction(self._parameters[index1],
                               fwd1, K1, t1)
        else:
            vol1 = vol0

        # In the expiry time dimension, both volatilities are interpolated
        # at the same strikes but different deltas.
        vart0 = vol0*vol0*t0
        vart1 = vol1*vol1*t1

        if np.abs(t1-t0) > 1e-6:

            vart = ((texp-t0) * vart1 + (t1-texp) * vart0) / (t1 - t0)
            kt = ((texp-t0) * K1 + (t1-texp) * K0) / (t1 - t0)

            if vart < 0.0:
                raise TuringError(
                    "Failed interpolation due to negative variance.")

            volt = np.sqrt(vart/texp)

        else:

            volt = vol0
            kt = K0

        return volt, kt

###############################################################################

    def _buildVolSurface(self, finSolverType=TuringSolverTypes.NELDER_MEAD, tol=1e-8):
        ''' Main function to construct the vol surface. '''

        s = self._spotFXRate
        numVolCurves = self._numVolCurves
        numParameters = 6
        self._parameters = np.zeros([numVolCurves, numParameters])

        numStrikes = 5
        self._strikes = np.zeros([numVolCurves, numStrikes])
        self._texp = np.zeros(numVolCurves)

        self._F0T = np.zeros(numVolCurves)
        self._rd = np.zeros(numVolCurves)
        self._rf = np.zeros(numVolCurves)
        self._K_ATM = np.zeros(numVolCurves)
        self._deltaATM = np.zeros(numVolCurves)

        self._K_25D_C = np.zeros(numVolCurves)
        self._K_25D_P = np.zeros(numVolCurves)

        self._K_10D_C = np.zeros(numVolCurves)
        self._K_10D_P = np.zeros(numVolCurves)

        #######################################################################
        # TODO: ADD SPOT DAYS
        #######################################################################
        spotDate = self._valueDate

        for i in range(0, numVolCurves):

            expiryDate = self._expiryDates[i]
            texp = (expiryDate - spotDate) / gDaysInYear

            domDF = self._domDiscountCurve._df(texp)
            forDF = self._forDiscountCurve._df(texp)
            f = s * forDF/domDF

            self._texp[i] = texp
            self._rd[i] = -np.log(domDF) / texp
            self._rf[i] = -np.log(forDF) / texp
            self._F0T[i] = f

            atmVol = self._atmVols[i]

            # This follows exposition in Clarke Page 52
            if self._atmMethod == TuringFXATMMethod.SPOT:
                self._K_ATM[i] = s
            elif self._atmMethod == TuringFXATMMethod.FWD:
                self._K_ATM[i] = f
            elif self._atmMethod == TuringFXATMMethod.FWD_DELTA_NEUTRAL:
                self._K_ATM[i] = f * np.exp(atmVol*atmVol*texp/2.0)
            elif self._atmMethod == TuringFXATMMethod.FWD_DELTA_NEUTRAL_PREM_ADJ:
                self._K_ATM[i] = f * np.exp(-atmVol*atmVol*texp/2.0)
            else:
                raise TuringError("Unknown Delta Type")

        #######################################################################
        # THE ACTUAL COMPUTATION LOOP STARTS HERE
        #######################################################################
        d25C = []
        d25ATM = []
        d25P = []
        d10C = []
        d10ATM = []
        d10P = []
        for i in range(0, numVolCurves):

            atmVol = self._atmVols[i]
            bf25 = self._butterfly25DeltaVols[i]
            rr25 = self._riskReversal25DeltaVols[i]

            bf10 = self._butterfly10DeltaVols[i]
            rr10 = self._riskReversal10DeltaVols[i]

            # https://quantpie.co.uk/fx/fx_rr_str.php

            d25C.append(atmVol + bf25 + rr25/2.0)  # 25D Call
            d25ATM.append(atmVol)                   # ATM
            d25P.append(atmVol + bf25 - rr25/2.0)  # 25D Put (75D Call)

            d10C.append(atmVol + bf10 + rr10/2.0)  # 10D Call
            d10ATM.append(atmVol)                    # ATM
            d10P.append(atmVol + bf10 - rr10/2.0)  # 10D Put (90D Call)

        deltaMethodValue = self._deltaMethod.value
        volTypeValue = self._volatilityFunctionType.value

        for i in range(0, numVolCurves):

            t = self._texp[i]
            rd = self._rd[i]
            rf = self._rf[i]
            K_ATM = self._K_ATM[i]
            atmVol = self._atmVols[i]

            # If the data has not been provided, pass a dummy value
            # as I don't want more arguments and Numpy needs floats
            if self._alpha > 0:
                bf25DVol = self._butterfly25DeltaVols[i]
                rr25DVol = self._riskReversal25DeltaVols[i]
            else:
                bf25DVol = -999.0
                rr25DVol = -999.0

            if self._alpha == 0:
                bf10DVol = self._butterfly10DeltaVols[i]
                rr10DVol = self._riskReversal10DeltaVols[i]
            else:
                bf10DVol = -999.0
                rr10DVol = -999.0

            res = _solveToHorizon(s, t, rd, rf,
                                  bf25DVol, bf10DVol, d25P[i],
                                  d25ATM[i], d25C[i], d10P[i], d10ATM[i],
                                  d10C[i])

            if bf25DVol != -999.0:
                self._K_25D_P[i], self._K_ATM[i], self._K_25D_C[i] = res
                params = [self._K_25D_P[i], self._K_ATM[i],
                          self._K_25D_C[i], d25P[i], d25ATM[i], d25C[i]]
                self._parameters[i, :] = np.array(params)
            elif bf10DVol != -999.0:
                self._K_10D_P[i], self._K_ATM[i], self._K_10D_C[i] = res
                params = [self._K_10D_P[i], self._K_ATM[i],
                          self._K_10D_C[i], d10P[i], d10ATM[i], d10C[i]]
                self._parameters[i, :] = np.array(params)
        # print("once", self._parameters)

###############################################################################

    def plotVolCurves(self):
        ''' Generates a plot of each of the vol curves implied by the market
        and fitted. '''

        plt.figure()

        volTypeVal = self._volatilityFunctionType.value

        for tenorIndex in range(0, self._numVolCurves):

            atmVol = self._atmVols[tenorIndex]*100
            bfVol25 = self._butterfly25DeltaVols[tenorIndex]*100
            rrVol25 = self._riskReversal25DeltaVols[tenorIndex]*100
            bfVol10 = self._butterfly10DeltaVols[tenorIndex]*100
            rrVol10 = self._riskReversal10DeltaVols[tenorIndex]*100
            strikes = self._strikes[tenorIndex]

            # gaps = self._gaps[tenorIndex]
            if self._alpha > 0:
                lowK = self._K_25D_P[tenorIndex] * 0.90
                highK = self._K_25D_C[tenorIndex] * 1.10
            else:
                lowK = self._K_10D_P[tenorIndex] * 0.90
                highK = self._K_10D_C[tenorIndex] * 1.10

            ks = []
            vols = []
            numIntervals = 30
            K = lowK
            dK = (highK - lowK)/numIntervals
            params = self._parameters[tenorIndex]
            t = self._texp[tenorIndex]
            f = self._F0T[tenorIndex]

            for i in range(0, numIntervals):
                sigma = volFunction(params, f, K, t) * 100.0
                ks.append(K)
                vols.append(sigma)
                K = K + dK

            labelStr = self._tenors[tenorIndex]
            labelStr += " ATM: " + str(atmVol)[0:6]
            labelStr += " MS25: " + str(bfVol25)[0:6]
            labelStr += " RR25: " + str(rrVol25)[0:6]
            labelStr += " MS10: " + str(bfVol10)[0:6]
            labelStr += " RR10: " + str(rrVol10)[0:6]

            plt.plot(ks, vols, label=labelStr)
            plt.xlabel("Strike")
            plt.ylabel("Volatility")

            title = "JNT FIT:" + self._currencyPair + " " +\
                    str(self._volatilityFunctionType)

            keyStrikes = []
            keyStrikes.append(self._K_ATM[tenorIndex])

            keyVols = []

            for K in keyStrikes:

                sigma = volFunction(params, f, K, t) * 100.0

                keyVols.append(sigma)

            plt.plot(keyStrikes, keyVols, 'ko', markersize=4)

            keyStrikes = []
            if self._alpha > 0:
                keyStrikes.append(self._K_25D_P[tenorIndex])
                keyStrikes.append(self._K_25D_C[tenorIndex])
            else:
                keyStrikes.append(self._K_10D_P[tenorIndex])
                keyStrikes.append(self._K_10D_C[tenorIndex])

            keyVols = []
            for K in keyStrikes:
                sigma = volFunction(params, f, K, t) * 100.0

                keyVols.append(sigma)

            plt.plot(keyStrikes, keyVols, 'bo', markersize=4)

        plt.title(title)
        plt.legend(loc="lower left", bbox_to_anchor=(1, 0))
        plt.show()

###############################################################################

    def __repr__(self):
        s = to_string("OBJECT TYPE", type(self).__name__)
        s += to_string("VALUE DATE", self._valueDate)
        s += to_string("FX RATE", self._spotFXRate)
        s += to_string("CCY PAIR", self._currencyPair)
        s += to_string("NUM TENORS", self._numVolCurves)
        s += to_string("ATM METHOD", self._atmMethod)
        s += to_string("DELTA METHOD", self._deltaMethod)
        s += to_string("ALPHA WEIGHT", self._alpha)
        s += to_string("VOL FUNCTION", self._volatilityFunctionType)

        for i in range(0, self._numVolCurves):

            s += "\n"

            s += to_string("TENOR", self._tenors[i])
            s += to_string("EXPIRY DATE", self._expiryDates[i])
            s += to_string("TIME (YRS)", self._texp[i])
            s += to_string("FWD FX", self._F0T[i])

            s += to_string("ATM VOLS", self._atmVols[i] * 100.0)
            s += to_string("BF VOLS", self._butterfly25DeltaVols[i] * 100.)
            s += to_string("RR VOLS", self._riskReversal25DeltaVols[i] * 100.)

            s += to_string("ATM Strike", self._K_ATM[i])
            s += to_string("ATM Delta", self._deltaATM[i])

            s += to_string("K_ATM", self._K_ATM[i])

            s += to_string("SKEW 25D CALL STRIKE", self._K_25D_C[i])
            s += to_string("SKEW 25D PUT STRIKE", self._K_25D_P[i])
            s += to_string("PARAMS", self._parameters[i])

            s += to_string("SKEW 10D CALL STRIKE", self._K_10D_C[i])
            s += to_string("SKEW 10D PUT STRIKE", self._K_10D_P[i])

        return s

###############################################################################

    def _print(self):
        ''' Print a list of the unadjusted coupon payment dates used in
        analytic calculations for the bond. '''
        print(self)

###############################################################################
