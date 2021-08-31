# TODO: Consider risk management
# TODO: Consider using Sobol
# TODO: Consider allowing weights on the individual basket assets
# TODO: Extend monte carlo to handle American options

import numpy as np

from turing_models.utilities.global_variables import gDaysInYear
from turing_models.models.gbm_process import TuringGBMProcess

from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import TuringOptionTypes, TuringKnockInTypes
from turing_models.utilities.helper_functions import to_string, checkArgumentTypes
from turing_models.utilities.helper_functions import _funcName
from turing_models.utilities.turing_date import TuringDate
from turing_models.market.curves.discount_curve import TuringDiscountCurve

from turing_models.utilities.mathematics import N


###############################################################################


class TuringSnowballBasketOption():
    ''' A TuringEquityBasketOption is a contract to buy a put or a call option on
    an equally weighted portfolio of different stocks, each with its own price,
    volatility and dividend yield. An analytical and monte-carlo pricing model
    have been implemented for a European style option. '''

    def __init__(self,
                 expiryDate: TuringDate,
                 optionType: TuringOptionTypes,
                 knock_out_price: float,
                 knock_in_price: float,
                 notional: float,
                 rebate: float,
                 numAssets: int,
                 coupon_annualized_flag: bool = True,
                 knock_in_type: TuringKnockInTypes = TuringKnockInTypes.RETURN,
                 knock_in_strike1: float = None,
                 knock_in_strike2: float = None,
                 participation_rate: float = 1.0):
        ''' Define the FinEquityBasket option by specifying its expiry date,
        its strike price, whether it is a put or call, and the number of
        underlying stocks in the basket. '''

        checkArgumentTypes(self.__init__, locals())

        if ((knock_in_strike1 is not None or knock_in_strike2 is not None) and
            knock_in_type == TuringKnockInTypes.RETURN) or \
           ((knock_in_strike1 is None or knock_in_strike2 is not None) and
            knock_in_type == TuringKnockInTypes.VANILLA) or \
           ((knock_in_strike1 is None or knock_in_strike2 is None) and
               knock_in_type == TuringKnockInTypes.SPREADS):
            raise TuringError("Mismatched strike inputs and knock_in type!")

        self._expiryDate = expiryDate
        self._optionType = optionType
        self._numAssets = numAssets
        self._k1 = knock_out_price
        self._k2 = knock_in_price
        self._notional = notional
        self._rebate = rebate
        self._flag = coupon_annualized_flag
        self._knock_in_type = knock_in_type
        self._sk1 = knock_in_strike1
        self._sk2 = knock_in_strike2
        self._participation_rate = participation_rate

###############################################################################

    def _validate(self,
                  stockPrices,
                  dividendYields,
                  volatilities,
                  correlations,
                  weights):

        if len(stockPrices) != self._numAssets:
            raise TuringError(
                "Stock prices must have a length " + str(self._numAssets))

        if len(dividendYields) != self._numAssets:
            raise TuringError(
                "Dividend yields must have a length " + str(self._numAssets))

        if len(volatilities) != self._numAssets:
            raise TuringError(
                "Volatilities must have a length " + str(self._numAssets))

        if len(weights) != self._numAssets:
            raise TuringError(
                "Weights must have a length " + str(self._numAssets))

        if np.sum(weights) != 1:
            raise TuringError(
                "Weights must sums to one ")

        if correlations.ndim != 2:
            raise TuringError(
                "Correlation must be a 2D matrix ")

        if correlations.shape[0] != self._numAssets:
            raise TuringError(
                "Correlation cols must have a length " + str(self._numAssets))

        if correlations.shape[1] != self._numAssets:
            raise TuringError(
                "correlation rows must have a length " + str(self._numAssets))

        for i in range(0, self._numAssets):
            if correlations[i, i] != 1.0:
                raise TuringError("Corr matrix must have 1.0 on the diagonal")

            for j in range(0, i):
                if abs(correlations[i, j]) > 1.0:
                    raise TuringError("Correlations must be [-1, +1]")

                if abs(correlations[j, i]) > 1.0:
                    raise TuringError("Correlations must be [-1, +1]")

                if correlations[i, j] != correlations[j, i]:
                    raise TuringError("Correlation matrix must be symmetric")

###############################################################################

    def valueMC(self,
                valueDate: TuringDate,
                stockPrices: np.ndarray,
                discountCurve: TuringDiscountCurve,
                dividendCurves: (list),
                volatilities: np.ndarray,
                corrMatrix: np.ndarray,
                weights: np.ndarray,
                numPaths: int = 10000,
                seed: int = 4242,
                num_ann_obs: int = 252):
        ''' Valuation of the EquityBasketOption using a Monte-Carlo simulation
        of stock prices assuming a GBM distribution. Cholesky decomposition is
        used to handle a full rank correlation structure between the individual
        assets. The numPaths and seed are pre-set to default values but can be
        overwritten. '''

        # checkArgumentTypes(getattr(self, _funcName(), None), locals())

        if valueDate > self._expiryDate:
            raise TuringError("Value date after expiry date.")

        texp = (self._expiryDate - valueDate) / gDaysInYear

        dividendYields = []
        for curve in dividendCurves:
            dq = curve.df(self._expiryDate)
            q = -np.log(dq) / texp
            dividendYields.append(q)

        self._validate(stockPrices,
                       dividendYields,
                       volatilities,
                       corrMatrix,
                       weights)

        numAssets = len(stockPrices)

        df = discountCurve.df(self._expiryDate)
        r = -np.log(df)/texp

        mus = r - dividendYields

        s0 = np.dot(stockPrices, weights)

        numTimeSteps = int(num_ann_obs * texp)

        process = TuringGBMProcess()
        np.random.seed(seed)

        Sall = process.getPathsAssets(numAssets,
                                      numPaths,
                                      numTimeSteps,
                                      texp,
                                      mus,
                                      stockPrices,
                                      volatilities,
                                      corrMatrix,
                                      seed)
        (num_paths, num_time_steps, _) = Sall.shape
        Sall_bskt = np.matmul(Sall,weights)

        out_call_sign = [False] * num_paths
        out_call_index = [False] * num_paths
        in_call_sign = [False] * num_paths
        out_put_sign = [False] * num_paths
        out_put_index = [False] * num_paths
        in_put_sign = [False] * num_paths

        # num_bus_days = int(252/12)
        num_bus_days = int(num_ann_obs / 12)

                # 生成一个标识索引的列表
        slice_length = (self._expiryDate._y - valueDate._y) * 12 + \
                       (self._expiryDate._m - valueDate._m) + \
                       (self._expiryDate._d > valueDate._d)
        index_list = list(range(num_time_steps))[::-num_bus_days][:slice_length][::-1]

        if self._optionType == TuringOptionTypes.SNOWBALL_CALL:
            for p in range(0, num_paths):
                out_call_sign[p] = np.any(Sall_bskt[p][::-num_bus_days][:slice_length] >= self._k1)

                if out_call_sign[p]:
                    for i in index_list:
                        if Sall_bskt[p][i] >= self._k1:
                            out_call_index[p] = i
                            break

                in_call_sign[p] = np.any(Sall_bskt[p] < self._k2)

        elif self._optionType == TuringOptionTypes.SNOWBALL_PUT:
            for p in range(0, num_paths):
                out_put_sign[p] = np.any(Sall_bskt[p][::-num_bus_days][:slice_length] <= self._k1)

                if out_put_sign[p]:
                    for i in index_list:
                        if Sall_bskt[p][i] <= self._k1:
                            out_put_index[p] = i
                            break

                in_put_sign[p] = np.any(Sall_bskt[p] > self._k2)

        ones = np.ones(num_paths)
        # list转成ndarray
        out_call_sign = np.array(out_call_sign)
        not_out_call_sign = ones - out_call_sign
        out_call_index = np.array(out_call_index)
        in_call_sign = np.array(in_call_sign)
        not_in_call_sign = ones - in_call_sign
        out_put_sign = np.array(out_put_sign)
        not_out_put_sign = ones - out_put_sign
        out_put_index = np.array(out_put_index)
        in_put_sign = np.array(in_put_sign)
        not_in_put_sign = ones - in_put_sign

        if self._optionType == TuringOptionTypes.SNOWBALL_CALL:

            payoff = out_call_sign * ((self._notional * self._rebate * (out_call_index / num_ann_obs)**self._flag) *
                     np.exp(-r * out_call_index / num_ann_obs)) + not_out_call_sign * not_in_call_sign * \
                     ((self._notional * self._rebate * texp**self._flag) * np.exp(-r * texp))

            if self._knock_in_type == TuringKnockInTypes.RETURN:
                payoff += not_out_call_sign * in_call_sign * \
                          (-self._notional * (1 - Sall_bskt[:, -1] / s0) *
                           self._participation_rate * np.exp(-r * texp))

            elif self._knock_in_type == TuringKnockInTypes.VANILLA:
                payoff += not_out_call_sign * in_call_sign * \
                          (-self._notional * np.maximum(self._sk1 - Sall_bskt[:, -1] / s0, 0) * \
                           self._participation_rate * texp**self._flag * np.exp(-r * texp))

            elif self._knock_in_type == TuringKnockInTypes.SPREADS:
                payoff += not_out_call_sign * in_call_sign * \
                          (-self._notional * np.maximum(self._sk1 - np.maximum(Sall_bskt[:, -1] / s0, self._sk2), 0) * \
                           self._participation_rate * texp**self._flag * np.exp(-r * texp))

        elif self._optionType == TuringOptionTypes.SNOWBALL_PUT:

            payoff = out_put_sign * ((self._notional * self._rebate * (out_put_index / num_ann_obs)**self._flag) *
                     np.exp(-r * out_put_index / num_ann_obs)) + not_out_put_sign * not_in_put_sign * \
                     ((self._notional * self._rebate * texp**self._flag) * np.exp(-r * texp))

            if self._knock_in_type == TuringKnockInTypes.RETURN:
                payoff += not_out_put_sign * in_put_sign * \
                          (-self._notional * (Sall_bskt[:, -1] / s0 - 1) * \
                           self._participation_rate * np.exp(-r * texp))

            elif self._knock_in_type == TuringKnockInTypes.VANILLA:
                payoff += not_out_put_sign * in_put_sign * \
                          (-self._notional * np.maximum(Sall_bskt[:, -1] / s0 - self._sk1, 0) * \
                           self._participation_rate * texp**self._flag * np.exp(-r * texp))

            elif self._knock_in_type == TuringKnockInTypes.SPREADS:
                payoff += not_out_put_sign * in_put_sign * \
                          (-self._notional * np.maximum(np.minimum(Sall_bskt[:, -1] / s0, self._sk2) - self._sk1, 0) * \
                           self._participation_rate * texp**self._flag * np.exp(-r * texp))

        return payoff.mean()


###############################################################################

    def __repr__(self):
        s = to_string("OBJECT TYPE", type(self).__name__)
        s += to_string("EXPIRY DATE", self._expiryDate)
        s += to_string("STRIKE PRICE", self._strikePrice)
        s += to_string("OPTION TYPE", self._optionType)
        s += to_string("NUM ASSETS", self._numAssets, "")
        return s

###############################################################################

    def _print(self):
        ''' Simple print function for backward compatibility. '''
        print(self)

###############################################################################