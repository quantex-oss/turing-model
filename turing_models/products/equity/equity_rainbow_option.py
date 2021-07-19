from math import exp, log, sqrt
import numpy as np
from typing import List

from turing_models.utilities.mathematics import N, M
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.error import TuringError
from turing_models.models.gbm_process import TuringGBMProcess
from turing_models.products.equity.equity_option import TuringEquityOption
from fundamental.market.curves.discount_curve import TuringDiscountCurve
from turing_models.utilities.helper_functions import label_to_string, checkArgumentTypes
from turing_models.utilities.turing_date import TuringDate

from enum import Enum


class TuringEquityRainbowOptionTypes(Enum):
    CALL_ON_MAXIMUM = 1
    PUT_ON_MAXIMUM = 2
    CALL_ON_MINIMUM = 3
    PUT_ON_MINIMUM = 4
    CALL_ON_NTH = 5  # MAX(NTH(S1,S2,...,SN)-K,0)
    PUT_ON_NTH = 6  # MAX(K-NTH(S1,S2,...,SN),0)

###############################################################################


def payoffValue(s, payoffTypeValue, payoffParams):

    if payoffTypeValue == TuringEquityRainbowOptionTypes.CALL_ON_MINIMUM.value:
        k = payoffParams[0]
        payoff = np.maximum(np.min(s, axis=1) - k, 0.0)
    elif payoffTypeValue == TuringEquityRainbowOptionTypes.CALL_ON_MAXIMUM.value:
        k = payoffParams[0]
        payoff = np.maximum(np.max(s, axis=1) - k, 0.0)
    elif payoffTypeValue == TuringEquityRainbowOptionTypes.PUT_ON_MINIMUM.value:
        k = payoffParams[0]
        payoff = np.maximum(k - np.min(s, axis=1), 0.0)
    elif payoffTypeValue == TuringEquityRainbowOptionTypes.PUT_ON_MAXIMUM.value:
        k = payoffParams[0]
        payoff = np.maximum(k - np.max(s, axis=1), 0.0)
    elif payoffTypeValue == TuringEquityRainbowOptionTypes.CALL_ON_NTH.value:
        n = payoffParams[0]
        k = payoffParams[1]
        ssorted = np.sort(s)
        assetn = ssorted[:, -n]
        payoff = np.maximum(assetn - k, 0.0)
    elif payoffTypeValue == TuringEquityRainbowOptionTypes.PUT_ON_NTH.value:
        n = payoffParams[0]
        k = payoffParams[1]
        ssorted = np.sort(s)
        assetn = ssorted[:, -n]
        payoff = np.maximum(k - assetn, 0.0)
    else:
        raise TuringError("Unknown payoff type")

    return payoff

###############################################################################


def valueMCFast(t,
                stockPrices,
                discountCurve,
                dividendCurves,
                volatilities,
                betas,
                numAssets,
                payoffType,
                payoffParams,
                numPaths=10000,
                seed=4242):

    np.random.seed(seed)

    df = discountCurve._df(t)
    r = -log(df)/t

    qs = []
    for curve in dividendCurves:
        dq = curve._df(t)
        q = -np.log(dq)/t
        qs.append(q)

    qs = np.array(qs)
    
    mus = r - qs

    model = TuringGBMProcess()

    numTimeSteps = 2
    Sall = model.getPathsAssets(numAssets, numPaths, numTimeSteps,
                                t, mus, stockPrices, volatilities, betas, seed)

    payoff = payoffValue(Sall, payoffType.value, payoffParams)
    payoff = np.mean(payoff)
    v = payoff * exp(-r * t)
    return v

###############################################################################


class TuringEquityRainbowOption(TuringEquityOption):

    def __init__(self,
                 expiryDate: TuringDate,
                 payoffType: TuringEquityRainbowOptionTypes,
                 payoffParams: List[float],
                 numAssets: int):

        checkArgumentTypes(self.__init__, locals())

        self._validatePayoff(payoffType, payoffParams, numAssets)

        self._expiryDate = expiryDate
        self._payoffType = payoffType
        self._payoffParams = payoffParams
        self._numAssets = numAssets

###############################################################################

    def _validate(self,
                  stockPrices,
                  dividendCurves,
                  volatilities,
                  betas):

        if len(stockPrices) != self._numAssets:
            raise TuringError(
                "Stock prices must be a vector of length "
                + str(self._numAssets))

        if len(dividendCurves) != self._numAssets:
            raise TuringError(
                "Dividend curves must be a vector of length "
                + str(self._numAssets))

        if len(volatilities) != self._numAssets:
            raise TuringError(
                "Volatilities must be a vector of length "
                + str(self._numAssets))

        if len(betas) != self._numAssets:
            raise TuringError("Betas must be a vector of length " +
                              str(self._numAssets))

###############################################################################

    def _validatePayoff(self, payoffType, payoffParams, numAssets):

        numParams = 0

        if payoffType == TuringEquityRainbowOptionTypes.CALL_ON_MINIMUM:
            numParams = 1
        elif payoffType == TuringEquityRainbowOptionTypes.CALL_ON_MAXIMUM:
            numParams = 1
        elif payoffType == TuringEquityRainbowOptionTypes.PUT_ON_MINIMUM:
            numParams = 1
        elif payoffType == TuringEquityRainbowOptionTypes.PUT_ON_MAXIMUM:
            numParams = 1
        elif payoffType == TuringEquityRainbowOptionTypes.CALL_ON_NTH:
            numParams = 2
        elif payoffType == TuringEquityRainbowOptionTypes.PUT_ON_NTH:
            numParams = 2
        else:
            raise TuringError("Unknown payoff type")

        if len(payoffParams) != numParams:
            raise TuringError(
                "Number of parameters required for " +
                str(payoffType) +
                " must be " +
                str(numParams))

        if payoffType == TuringEquityRainbowOptionTypes.CALL_ON_NTH \
           or payoffType == TuringEquityRainbowOptionTypes.PUT_ON_NTH:
            n = payoffParams[0]
            if n < 1 or n > numAssets:
                raise TuringError("Nth parameter must be 1 to " + str(numAssets))

###############################################################################

    def value(self,
              valueDate: TuringDate,
              stockPrices: np.ndarray,
              discountCurve: TuringDiscountCurve,
              dividendCurves: (list),
              volatilities: np.ndarray,
              corrMatrix: np.ndarray):

        if self._numAssets != 2:
            raise TuringError("Analytical results for two assets only.")

        if corrMatrix.ndim != 2:
            raise TuringError("Corr matrix must be of size 2x2")

        if corrMatrix.shape[0] != 2:
            raise TuringError("Corr matrix must be of size 2x2")

        if corrMatrix.shape[1] != 2:
            raise TuringError("Corr matrix must be of size 2x2")

        if valueDate > self._expiryDate:
            raise TuringError("Value date after expiry date.")


        # Use result by Stulz (1982) given by Haug Page 211
        t = (self._expiryDate - valueDate) / gDaysInYear
        r = discountCurve.zeroRate(self._expiryDate)

        q1 = dividendCurves[0].zeroRate(self._expiryDate)
        q2 = dividendCurves[1].zeroRate(self._expiryDate)

        dividendYields = [q1, q2]

        self._validate(stockPrices,
                       dividendYields,
                       volatilities,
                       corrMatrix)

#        q1 = dividendYields[0]
#        q2 = dividendYields[1]

        rho = corrMatrix[0][1]
        s1 = stockPrices[0]
        s2 = stockPrices[1]
        b1 = r - q1
        b2 = r - q2
        v1 = volatilities[0]
        v2 = volatilities[1]
        k = self._payoffParams[0]

        v = sqrt(v1 * v1 + v2 * v2 - 2 * rho * v1 * v2)
        d = (log(s1 / s2) + (b1 - b2 + v * v / 2) * t) / v / sqrt(t)
        y1 = (log(s1 / k) + (b1 + v1 * v1 / 2) * t) / v1 / sqrt(t)
        y2 = (log(s2 / k) + (b2 + v2 * v2 / 2) * t) / v2 / sqrt(t)
        rho1 = (v1 - rho * v2) / v
        rho2 = (v2 - rho * v1) / v
        dq1 = exp(-q1 * t)
        dq2 = exp(-q2 * t)
        df = exp(-r * t)

        if self._payoffType == TuringEquityRainbowOptionTypes.CALL_ON_MAXIMUM:
            v = s1 * dq1 * M(y1, d, rho1) + s2 * dq2 * M(y2, -d + v * sqrt(t), rho2) \
                - k * df * (1.0 - M(-y1 + v1 * sqrt(t), -y2 + v2 * sqrt(t), rho))
        elif self._payoffType == TuringEquityRainbowOptionTypes.CALL_ON_MINIMUM:
            v = s1 * dq1 * M(y1, -d, -rho1) + s2 * dq2 * M(y2, d - v * sqrt(t), -rho2) \
                - k * df * M(y1 - v1 * sqrt(t), y2 - v2 * sqrt(t), rho)
        elif self._payoffType == TuringEquityRainbowOptionTypes.PUT_ON_MAXIMUM:
            cmax1 = s2 * dq2 + s1 * dq1 * N(d) - s2 * dq2 * N(d - v * sqrt(t))
            cmax2 = s1 * dq1 * M(y1, d, rho1) + s2 * dq2 * M(y2, -d + v * sqrt(t), rho2) \
                - k * df * (1.0 - M(-y1 + v1 * sqrt(t), -y2 + v2 * sqrt(t), rho))
            v = k * df - cmax1 + cmax2
        elif self._payoffType == TuringEquityRainbowOptionTypes.PUT_ON_MINIMUM:
            cmin1 = s1 * dq1 - s1 * dq1 * N(d) + s2 * dq2 * N(d - v * sqrt(t))
            cmin2 = s1 * dq1 * M(y1, -d, -rho1) + s2 * dq2 * M(y2, d - v * sqrt(
                t), -rho2) - k * df * M(y1 - v1 * sqrt(t), y2 - v2 * sqrt(t), rho)
            v = k * df - cmin1 + cmin2
        else:
            raise TuringError("Unsupported Rainbow option type")

        return v

###############################################################################

    def valueMC(self,
                valueDate,
                stockPrices,
                discountCurve,
                dividendCurves,
                volatilities,
                corrMatrix,
                numPaths=10000,
                seed=4242):

        self._validate(stockPrices,
                       dividendCurves,
                       volatilities,
                       corrMatrix)

        if valueDate > self._expiryDate:
            raise TuringError("Value date after expiry date.")

        t = (self._expiryDate - valueDate) / gDaysInYear

        v = valueMCFast(t,
                        stockPrices,
                        discountCurve,
                        dividendCurves,
                        volatilities,
                        corrMatrix,
                        self._numAssets,
                        self._payoffType,
                        self._payoffParams,
                        numPaths,
                        seed)

        return v

###############################################################################

    def __repr__(self):

        s = label_to_string("OBJECT TYPE", type(self).__name__)
        s += label_to_string("EXPIRY DATE", self._expiryDate)
        s += label_to_string("PAYOFF TYPE", self._payoffType)
        s += label_to_string("PAYOFF PARAMS", self._payoffParams)
        s += label_to_string("NUM ASSETS TYPE", self._numAssets, "")
        return s

###############################################################################

    def _print(self):
        ''' Simple print function for backward compatibility. '''
        print(self)

###############################################################################
