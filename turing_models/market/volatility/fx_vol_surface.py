import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from numba import njit, float64, int64

from turing_models.utilities.error import TuringError
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.utilities.solvers_1d import newton_secant
from turing_models.utilities.distribution import TuringDistribution
from turing_models.utilities.mathematics import norminvcdf
from turing_models.utilities.helper_functions import checkArgumentTypes, to_string, fastDelta
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.models.model_option_implied_dbn import optionImpliedDbn
from turing_models.models.model_volatility_fns import volFunctionClark, volFunctionBloomberg, \
     TuringVolFunctionTypes
from turing_models.models.model_sabr import volFunctionSABR, volFunctionSABR_BETA_ONE, volFunctionSABR_BETA_HALF
from turing_models.models.model_black_scholes_analytical import bs_value
from turing_models.instruments.common import TuringFXATMMethod, TuringFXDeltaMethod

###############################################################################
# TODO: Speed up search for strike by providing derivative function to go with
#       delta fit.
###############################################################################


@njit(fastmath=True, cache=True)
def g(K, *args):
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
# Do not cache this function


@njit(fastmath=True)  # , cache=True)
def objFAST(params, *args):
    ''' Return a function that is minimised when the ATM, MS and RR vols have
    been best fitted using the parametric volatility curve represented by cvec
    '''

    s = args[0]
    t = args[1]
    rd = args[2]
    rf = args[3]
    K_ATM = args[4]
    atmVol = args[5]
    K_25D_C_MS = args[6]
    K_25D_P_MS = args[7]
    V_25D_MS_target = args[8]
    deltaMethodValue = args[9]
    targetRRVol = args[10]
    volTypeValue = args[11]

    f = s * np.exp((rd-rf)*t)
    # We first need to solve for the strikes at the 25 delta points using the
    # new volatility curve

    # Match the at-the-money option volatility
    atmCurveVol = volFunction(volTypeValue, params, f, K_ATM, t)
    term1 = (atmVol - atmCurveVol)**2

    ###########################################################################
    # Match the market strangle value but this has to be at the MS strikes
    ###########################################################################

    sigma_K_25D_C_MS = volFunction(volTypeValue, params, f, K_25D_C_MS, t)

    V_25D_C_MS = bs_value(s, t, K_25D_C_MS, rd, rf, sigma_K_25D_C_MS,
                          TuringOptionTypes.EUROPEAN_CALL.value, False)

    sigma_K_25D_P_MS = volFunction(volTypeValue, params, f, K_25D_P_MS, t)

    V_25D_P_MS = bs_value(s, t, K_25D_P_MS, rd, rf, sigma_K_25D_P_MS,
                          TuringOptionTypes.EUROPEAN_PUT.value, False)

    V_25D_MS = V_25D_C_MS + V_25D_P_MS
    term2 = (V_25D_MS - V_25D_MS_target)**2

    ###########################################################################
    # Match the risk reversal volatility
    ###########################################################################

    K_25D_C = solveForSmileStrikeFAST(s, t, rd, rf,
                                      TuringOptionTypes.EUROPEAN_CALL.value,
                                      volTypeValue, +0.2500,
                                      deltaMethodValue, K_25D_C_MS,
                                      params)

    sigma_K_25D_C = volFunction(volTypeValue, params, f, K_25D_C, t)

    K_25D_P = solveForSmileStrikeFAST(s, t, rd, rf,
                                      TuringOptionTypes.EUROPEAN_PUT.value,
                                      volTypeValue, -0.2500,
                                      deltaMethodValue, K_25D_P_MS,
                                      params)

    sigma_K_25D_P = volFunction(volTypeValue, params, f, K_25D_P, t)

    sigma_25D_RR = (sigma_K_25D_C - sigma_K_25D_P)
    term3 = (sigma_25D_RR - targetRRVol)**2

    # sum up the errors
    err = term1 + term2 + term3

    return err

###############################################################################
# This function cannot be jitted until the scipy minimisation has been replaced
# with a jittable function


def solveToHorizonFAST(s, t,
                       rd, rf,
                       K_ATM, atmVol,
                       ms25DVol, rr25DVol,
                       deltaMethodValue, volTypeValue,
                       xopt):

    c0 = xopt

    # Determine the price of a market strangle from market strangle
    # Need to price a call and put that agree with market strangle

    vol_25D_MS = atmVol + ms25DVol

    K_25D_C_MS = solveForStrike(s, t, rd, rf,
                                TuringOptionTypes.EUROPEAN_CALL.value,
                                +0.2500,
                                deltaMethodValue,
                                vol_25D_MS)

    K_25D_P_MS = solveForStrike(s, t, rd, rf,
                                TuringOptionTypes.EUROPEAN_PUT.value,
                                -0.2500,
                                deltaMethodValue,
                                vol_25D_MS)

    # USE MARKET STRANGLE VOL TO DETERMINE PRICE OF A MARKET STRANGLE
    V_25D_C_MS = bs_value(s, t, K_25D_C_MS, rd, rf, vol_25D_MS,
                          TuringOptionTypes.EUROPEAN_CALL.value, False)

    V_25D_P_MS = bs_value(s, t, K_25D_P_MS, rd, rf, vol_25D_MS,
                          TuringOptionTypes.EUROPEAN_PUT.value, False)

    # Market price of strangle in the domestic currency
    V_25D_MS = V_25D_C_MS + V_25D_P_MS

    # Determine parameters of vol surface using minimisation
    tol = 1e-8

    fargs = (s, t, rd, rf,
             K_ATM, atmVol,
             K_25D_C_MS, K_25D_P_MS,
             V_25D_MS,
             deltaMethodValue, rr25DVol, volTypeValue)

    opt = minimize(objFAST, c0, fargs, method="CG", tol=tol)
    xopt = opt.x

    params = np.array(xopt)

    K_25D_C = solveForSmileStrikeFAST(s, t, rd, rf,
                                      TuringOptionTypes.EUROPEAN_CALL.value,
                                      volTypeValue, +0.2500,
                                      deltaMethodValue, K_25D_C_MS,
                                      params)

    K_25D_P = solveForSmileStrikeFAST(s, t, rd, rf,
                                      TuringOptionTypes.EUROPEAN_PUT.value,
                                      volTypeValue, -0.2500,
                                      deltaMethodValue, K_25D_P_MS,
                                      params)

    ret = (params, K_25D_C_MS, K_25D_P_MS, K_25D_C, K_25D_P)
    return ret

###############################################################################


@njit(float64(int64, float64[:], float64, float64, float64),
      cache=True, fastmath=True)
def volFunction(volFunctionTypeValue, params, f, k, t):
    ''' Return the volatility for a strike using a given polynomial
    interpolation following Section 3.9 of Iain Clark book. '''

    if volFunctionTypeValue == TuringVolFunctionTypes.CLARK.value:
        vol = volFunctionClark(params, f, k, t)
        return vol
    elif volFunctionTypeValue == TuringVolFunctionTypes.SABR.value:
        vol = volFunctionSABR(params, f, k, t)
        return vol
    elif volFunctionTypeValue == TuringVolFunctionTypes.SABR_BETA_ONE.value:
        vol = volFunctionSABR_BETA_ONE(params, f, k, t)
        return vol
    elif volFunctionTypeValue == TuringVolFunctionTypes.SABR_BETA_HALF.value:
        vol = volFunctionSABR_BETA_HALF(params, f, k, t)
        return vol
    elif volFunctionTypeValue == TuringVolFunctionTypes.BBG.value:
        vol = volFunctionBloomberg(params, f, k, t)
        return vol
    elif volFunctionTypeValue == TuringVolFunctionTypes.CLARK5.value:
        vol = volFunctionClark(params, f, k, t)
        return vol
    else:
        raise TuringError("Unknown Model Type")

###############################################################################


@njit(cache=True, fastmath=True)
def deltaFit(K, *args):
    ''' This is the objective function used in the determination of the FX
    Option implied strike which is computed in the class below. I map it into
    inverse normcdf space to avoid the flat slope of this function at low vol
    and high K. It speeds up the code as it allows initial values close to
    the solution to be used. '''

    volTypeValue = args[0]
    s = args[1]
    t = args[2]
    rd = args[3]
    rf = args[4]
    optionTypeValue = args[5]
    deltaTypeValue = args[6]
    inverseDeltaTarget = args[7]
    params = args[8]

    f = s*np.exp((rd-rf)*t)
    v = volFunction(volTypeValue, params, f, K, t)
    deltaOut = fastDelta(s, t, K, rd, rf, v, deltaTypeValue, optionTypeValue)
    inverseDeltaOut = norminvcdf(np.abs(deltaOut))
    invObjFn = inverseDeltaTarget - inverseDeltaOut

    return invObjFn

###############################################################################
# Unable to cache this function due to dynamic globals warning. Revisit.


@njit(float64(float64, float64, float64, float64, int64, int64, float64,
              int64, float64, float64[:]), fastmath=True)
def solveForSmileStrikeFAST(s, t, rd, rf,
                            optionTypeValue,
                            volatilityTypeValue,
                            deltaTarget,
                            deltaMethodValue,
                            initialGuess,
                            parameters):
    ''' Solve for the strike that sets the delta of the option equal to the
    target value of delta allowing the volatility to be a function of the
    strike. '''

    inverseDeltaTarget = norminvcdf(np.abs(deltaTarget))

    argtuple = (volatilityTypeValue, s, t, rd, rf, optionTypeValue,
                deltaMethodValue, inverseDeltaTarget, parameters)

    K = newton_secant(deltaFit, x0=initialGuess, args=argtuple,
                      tol=1e-8, maxiter=50)

    return K

###############################################################################
# Unable to cache function


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
        K = F0T * np.exp(-vsqrtt * (phi*norminvdelta - vsqrtt/2.0))
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
        arg = deltaTarget*phi   # CHECK THIS!!!!!!!!
        norminvdelta = norminvcdf(arg)
        K = F0T * np.exp(-vsqrtt * (phi*norminvdelta - vsqrtt/2.0))
        return K

    elif deltaMethodValue == TuringFXDeltaMethod.SPOT_DELTA_PREM_ADJ.value:

        argtuple = (spotFXRate, tdel, rd, rf, volatility,
                    deltaMethodValue, optionTypeValue, deltaTarget)

        K = newton_secant(g, x0=spotFXRate, args=argtuple,
                          tol=1e-7, maxiter=50)

        return K

    elif deltaMethodValue == TuringFXDeltaMethod.FORWARD_DELTA_PREM_ADJ.value:

        argtuple = (spotFXRate, tdel, rd, rf, volatility,
                    deltaMethodValue, optionTypeValue, deltaTarget)

        K = newton_secant(g, x0=spotFXRate, args=argtuple,
                          tol=1e-7, maxiter=50)

        return K

    else:

        raise TuringError("Unknown TuringFXDeltaMethod")

###############################################################################


class TuringFXVolSurface():
    ''' Class to perform a calibration of a chosen parametrised surface to the
    prices of FX options at different strikes and expiry tenors. The
    calibration inputs are the ATM and 25 Delta volatilities given in terms of
    the market strangle amd risk reversals. There is a choice of volatility
    function ranging from polynomial in delta to a limited version of SABR. '''

    def __init__(self,
                 valueDate: TuringDate,
                 spotFXRate: float,
                 currencyPair: str,
                 notionalCurrency: str,
                 domDiscountCurve: TuringDiscountCurve,
                 forDiscountCurve: TuringDiscountCurve,
                 tenors: (list),
                 atmVols: (list, np.ndarray),
                 mktStrangle25DeltaVols: (list, np.ndarray),
                 riskReversal25DeltaVols: (list, np.ndarray),
                 atmMethod: TuringFXATMMethod = TuringFXATMMethod.FWD_DELTA_NEUTRAL,
                 deltaMethod: TuringFXDeltaMethod = TuringFXDeltaMethod.SPOT_DELTA,
                 volatilityFunctionType: TuringVolFunctionTypes = TuringVolFunctionTypes.CLARK):
        ''' Create the TuringFXVolSurface object by passing in market vol data
        for ATM and 25 Delta Market Strangles and Risk Reversals. '''

        checkArgumentTypes(self.__init__, locals())

        self._valueDate = valueDate
        self._spotFXRate = spotFXRate
        self._currencyPair = currencyPair

        if len(currencyPair) != 6:
            raise TuringError("Currency pair must be 6 characters.")

        self._forName = self._currencyPair[0:3]
        self._domName = self._currencyPair[3:6]

        self._notionalCurrency = notionalCurrency
        self._domDiscountCurve = domDiscountCurve
        self._forDiscountCurve = forDiscountCurve
        self._numVolCurves = len(tenors)

        if len(atmVols) != self._numVolCurves:
            raise TuringError("Number ATM vols must equal number of tenors")

        if len(atmVols) != self._numVolCurves:
            raise TuringError("Number ATM vols must equal number of tenors")

        if len(mktStrangle25DeltaVols) != self._numVolCurves:
            raise TuringError("Number MS25D vols must equal number of tenors")

        if len(riskReversal25DeltaVols) != self._numVolCurves:
            raise TuringError("Number RR25D vols must equal number of tenors")

        self._tenors = tenors
        self._atmVols = np.array(atmVols)/100.0
        self._mktStrangle25DeltaVols = np.array(mktStrangle25DeltaVols)/100.0
        self._riskReversal25DeltaVols = np.array(riskReversal25DeltaVols)/100.0

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
        for i in range(0, self._numVolCurves):
            expiryDate = valueDate.addTenor(tenors[i])
            self._expiryDates.append(expiryDate)

        self.buildVolSurface()

###############################################################################

    def volatility(self, K, expiryDate):
        ''' Interpolate the Black-Scholes volatility from the volatility
        surface given the option strike and expiry date. Linear interpolation
        is done in variance x time. '''

        volTypeValue = self._volatilityFunctionType.value

        index0 = 0
        index1 = 0

        t = (expiryDate - self._valueDate) / gDaysInYear

        numCurves = self._numVolCurves

        if numCurves == 1:

            # The volatility term structure is flat if there is only one expiry
            fwd = self._F0T[0]
            texp = self._texp[0]
            vol = volFunction(volTypeValue, self._parameters[0],
                              fwd, K, texp)
            return vol

        # If the time is below first time then assume a flat vol
        if t <= self._texp[0]:

            fwd = self._F0T[0]
            texp = self._texp[0]
            vol = volFunction(volTypeValue, self._parameters[0],
                              fwd, K, texp)
            return vol

        # If the time is beyond the last time then extrapolate with a flat vol
        if t > self._texp[-1]:

            fwd = self._F0T[-1]
            texp = self._texp[-1]
            vol = volFunction(volTypeValue, self._parameters[-1],
                              fwd, K, texp)
            return vol

        for i in range(1, numCurves):

            if t <= self._texp[i] and t > self._texp[i-1]:
                index0 = i-1
                index1 = i
                break

        fwd0 = self._F0T[index0]
        t0 = self._texp[index0]
        vol0 = volFunction(volTypeValue, self._parameters[index0],
                           fwd0, K, t0)

        fwd1 = self._F0T[index1]
        t1 = self._texp[index1]
        vol1 = volFunction(volTypeValue, self._parameters[index1],
                           fwd1, K, t1)

        vart0 = vol0*vol0*t0
        vart1 = vol1*vol1*t1
        vart = ((t-t0) * vart1 + (t1-t) * vart0) / (t1 - t0)

        if vart < 0.0:
            raise TuringError("Negative variance.")

        volt = np.sqrt(vart/t)
        return volt

###############################################################################

    def buildVolSurface(self):

        s = self._spotFXRate
        numVolCurves = self._numVolCurves

        if self._volatilityFunctionType == TuringVolFunctionTypes.CLARK:
            numParameters = 3
        elif self._volatilityFunctionType == TuringVolFunctionTypes.SABR:
            numParameters = 4
        elif self._volatilityFunctionType == TuringVolFunctionTypes.SABR_BETA_ONE:
            numParameters = 3
        elif self._volatilityFunctionType == TuringVolFunctionTypes.SABR_BETA_HALF:
            numParameters = 3
        elif self._volatilityFunctionType == TuringVolFunctionTypes.BBG:
            numParameters = 3
        elif self._volatilityFunctionType == TuringVolFunctionTypes.CLARK5:
            numParameters = 5
        else:
            print(self._volatilityFunctionType)
            raise TuringError("Unknown Model Type")

        self._parameters = np.zeros([numVolCurves, numParameters])

        self._F0T = np.zeros(numVolCurves)
        self._rd = np.zeros(numVolCurves)
        self._rf = np.zeros(numVolCurves)
        self._K_ATM = np.zeros(numVolCurves)
        self._deltaATM = np.zeros(numVolCurves)

        self._K_25D_C = np.zeros(numVolCurves)
        self._K_25D_P = np.zeros(numVolCurves)
        self._K_25D_C_MS = np.zeros(numVolCurves)
        self._K_25D_P_MS = np.zeros(numVolCurves)
        self._V_25D_MS = np.zeros(numVolCurves)
        self._texp = np.zeros(numVolCurves)

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

        xinits = []
        for i in range(0, numVolCurves):

            atmVol = self._atmVols[i]
            ms25 = self._mktStrangle25DeltaVols[i]
            rr25 = self._riskReversal25DeltaVols[i]
            s25 = atmVol + ms25 + rr25/2.0
            s50 = atmVol
            s75 = atmVol + ms25 - rr25/2.0

            if self._volatilityFunctionType == TuringVolFunctionTypes.CLARK:

                # Fit to 25D
                c0 = np.log(atmVol)
                c1 = 2.0 * np.log(s75/s25)
                c2 = 8.0 * np.log(s25*s75/atmVol/atmVol)
                xinit = [c0, c1, c2]

            elif self._volatilityFunctionType == TuringVolFunctionTypes.SABR:
                # SABR parameters are alpha, nu, rho
                # SABR parameters are alpha, nu, rho
                alpha = 0.174
                beta = 1.0
                rho = -0.112
                nu = 0.817

                xinit = [alpha, beta, rho, nu]

            elif self._volatilityFunctionType == TuringVolFunctionTypes.SABR_BETA_ONE:
                # SABR parameters are alpha, nu, rho
                alpha = 0.174
                rho = -0.112
                nu = 0.817
                xinit = [alpha, nu, rho]

            elif self._volatilityFunctionType == TuringVolFunctionTypes.SABR_BETA_HALF:
                # SABR parameters are alpha, nu, rho
                alpha = 0.174
                rho = -0.112
                nu = 0.817
                xinit = [alpha, rho, nu]

            elif self._volatilityFunctionType == TuringVolFunctionTypes.BBG:

                # BBG Params if we fit to 25D
                a = 8.0*s75-16.0*s50+8.0*s25
                b = -6.0*s75+16.0*s50-10.0*s25
                c = s75-3.0*s50+3.0*s25

                xinit = [a, b, c]

            elif self._volatilityFunctionType == TuringVolFunctionTypes.CLARK5:

                # Fit to 25D
                c0 = np.log(atmVol)
                c1 = 2.0 * np.log(s75/s25)
                c2 = 8.0 * np.log(s25*s75/atmVol/atmVol)
                xinit = [c0, c1, c2, 0.0, 0.0]

            else:
                raise TuringError("Unknown Model Type")

            xinits.append(xinit)

        deltaMethodValue = self._deltaMethod.value
        volTypeValue = self._volatilityFunctionType.value

        for i in range(0, numVolCurves):

            t = self._texp[i]
            rd = self._rd[i]
            rf = self._rf[i]
            K_ATM = self._K_ATM[i]
            atmVol = self._atmVols[i]
            ms25DVol = self._mktStrangle25DeltaVols[i]
            rr25DVol = self._riskReversal25DeltaVols[i]

#            print(t, rd, rf, K_ATM, atmVol, ms25DVol, rr25DVol)

            res = solveToHorizonFAST(s, t, rd, rf, K_ATM,
                                     atmVol, ms25DVol, rr25DVol,
                                     deltaMethodValue, volTypeValue,
                                     xinits[i])

            (self._parameters[i, :],
             self._K_25D_C_MS[i], self._K_25D_P_MS[i],
             self._K_25D_C[i], self._K_25D_P[i]) = res

###############################################################################

    def solveForSmileStrike(self,
                            optionTypeValue,
                            deltaTarget,
                            tenorIndex,
                            initialValue):
        ''' Solve for the strike that sets the delta of the option equal to the
        target value of delta allowing the volatility to be a function of the
        strike. '''

        s0 = self._spotFXRate
        tdel = self._texp[tenorIndex]
        rd = self._rd[tenorIndex]
        rf = self._rf[tenorIndex]

        inverseDeltaTarget = norminvcdf(np.abs(deltaTarget))
        argtuple = (self, s0, tdel, rd, rf, optionTypeValue,
                    inverseDeltaTarget, tenorIndex)

        volTypeValue = self._volatilityFunctionType.value

        argtuple = (volTypeValue, s0, tdel, rd, rf, optionTypeValue,
                    self._deltaMethod.value,
                    inverseDeltaTarget, self._parameters[tenorIndex])

        K = newton_secant(deltaFit, x0=initialValue, args=argtuple,
                          tol=1e-5, maxiter=50)

        return K

###############################################################################

    def impliedDbns(self, lowFX, highFX, numIntervals):
        ''' Calculate the pdf for each tenor horizon. Returns a list of
        TuringDistribution objects, one for each tenor horizon. '''

        dbns = []

        for iTenor in range(0, len(self._tenors)):

            f = self._F0T[iTenor]
            texp = self._texp[iTenor]

            dFX = (highFX - lowFX) / numIntervals

            domDF = self._domDiscountCurve._df(texp)
            forDF = self._forDiscountCurve._df(texp)

            rd = -np.log(domDF) / texp
            rf = -np.log(forDF) / texp

            Ks = []
            vols = []

            for iK in range(0, numIntervals):

                k = lowFX + iK*dFX

                vol = volFunction(self._volatilityFunctionType.value,
                                  self._parameters[iTenor],
                                  f, k, texp)

                Ks.append(k)
                vols.append(vol)

            Ks = np.array(Ks)
            vols = np.array(vols)

            density = optionImpliedDbn(self._spotFXRate, texp,
                                       rd, rf, Ks, vols)

            dbn = TuringDistribution(Ks, density)
            dbns.append(dbn)

        return dbns

###############################################################################

    def plotVolCurves(self):

        plt.figure()

        volTypeVal = self._volatilityFunctionType.value

        for tenorIndex in range(0, self._numVolCurves):

            atmVol = self._atmVols[tenorIndex]*100
            msVol = self._mktStrangle25DeltaVols[tenorIndex]*100
            rrVol = self._riskReversal25DeltaVols[tenorIndex]*100

            lowK = self._K_25D_P[tenorIndex] * 0.75
            highK = self._K_25D_C[tenorIndex] * 1.25

            strikes = []
            vols = []
            numIntervals = 30
            K = lowK
            dK = (highK - lowK)/numIntervals
            params = self._parameters[tenorIndex]
            t = self._texp[tenorIndex]
            f = self._F0T[tenorIndex]

            for _ in range(0, numIntervals):
                sigma = volFunction(volTypeVal, params, f, K, t) * 100.0
                strikes.append(K)
                vols.append(sigma)
                K = K + dK

            labelStr = self._tenors[tenorIndex]
            labelStr += " ATM: " + str(atmVol)[0:6]
            labelStr += " MS: " + str(msVol)[0:6]
            labelStr += " RR: " + str(rrVol)[0:6]

            plt.plot(strikes, vols, label=labelStr)
            plt.xlabel("Strike")
            plt.ylabel("Volatility")

            title = "25D FIT:" + self._currencyPair + \
                " " + str(self._volatilityFunctionType)

            keyStrikes = []
            keyStrikes.append(self._K_ATM[tenorIndex])

            keyVols = []
            for K in keyStrikes:
                sigma = volFunction(volTypeVal, params, f, K, t) * 100.0
                keyVols.append(sigma)

            plt.plot(keyStrikes, keyVols, 'ko', markersize=4)

            keyStrikes = []
            keyStrikes.append(self._K_25D_P[tenorIndex])
            keyStrikes.append(self._K_25D_P_MS[tenorIndex])
            keyStrikes.append(self._K_25D_C[tenorIndex])
            keyStrikes.append(self._K_25D_C_MS[tenorIndex])

            keyVols = []

            for K in keyStrikes:
                sigma = volFunction(volTypeVal, params, f, K, t) * 100.0
                keyVols.append(sigma)

            plt.plot(keyStrikes, keyVols, 'bo', markersize=4)

        plt.title(title)
#        plt.legend(loc="lower left", bbox_to_anchor=(1,0))

###############################################################################

    def __repr__(self):
        s = to_string("OBJECT TYPE", type(self).__name__)
        s += to_string("VALUE DATE", self._valueDate)
        s += to_string("FX RATE", self._spotFXRate)
        s += to_string("CCY PAIR", self._currencyPair)
        s += to_string("NOTIONAL CCY", self._notionalCurrency)
        s += to_string("NUM TENORS", self._numVolCurves)
        s += to_string("ATM METHOD", self._atmMethod)
        s += to_string("DELTA METHOD", self._deltaMethod)
        s += to_string("VOL FUNCTION", self._volatilityFunctionType)

        for i in range(0, self._numVolCurves):

            s += "\n"

            s += to_string("TENOR", self._tenors[i])
            s += to_string("EXPIRY DATE", self._expiryDates[i])
            s += to_string("TIME (YRS)", self._texp[i])
            s += to_string("FWD FX", self._F0T[i])

            s += to_string("ATM VOLS", self._atmVols[i] * 100.0)
            s += to_string("MS VOLS", self._mktStrangle25DeltaVols[i] * 100.0)
            s += to_string("RR VOLS", self._riskReversal25DeltaVols[i] * 100.0)

            s += to_string("ATM Strike", self._K_ATM[i])
            s += to_string("ATM Delta", self._deltaATM[i])

            s += to_string("K_ATM", self._K_ATM[i])
            s += to_string("MS 25D Call Strike", self._K_25D_C_MS[i])
            s += to_string("MS 25D Put Strike", self._K_25D_P_MS[i])
            s += to_string("SKEW 25D CALL STRIKE", self._K_25D_C[i])
            s += to_string("SKEW 25D PUT STRIKE", self._K_25D_P[i])
            s += to_string("PARAMS", self._parameters[i])

        return s

###############################################################################

    def _print(self):
        ''' Print a list of the unadjusted coupon payment dates used in
        analytic calculations for the bond. '''
        print(self)

###############################################################################
