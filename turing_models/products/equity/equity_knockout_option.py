import numpy as np
from enum import Enum

from turing_models.utilities import TuringKnockOutTypes
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.products.equity.equity_option import TuringEquityOption
from turing_models.models.process_simulator import TuringProcessSimulator, TuringProcessTypes, \
     TuringGBMNumericalScheme, TuringHestonNumericalScheme
from turing_models.models.model_black_scholes import TuringModel
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.utilities.helper_functions import to_string, checkArgumentTypes
from turing_models.utilities.turing_date import TuringDate


###############################################################################


###############################################################################


class TuringEquityKnockoutOption(TuringEquityOption):
    ''' Class to hold details of an Equity Knockout Option. '''

    def __init__(self,
                 expiry_date: TuringDate,
                 strike_price: float,
                 knock_out_type: TuringKnockOutTypes,
                 barrier: float,
                 rebate: float,
                 coupon_annualized_flag: bool = True,
                 notional: float = 1.0,
                 participation_rate: float = 1.0,
                 num_observations_per_year: int = 252):
        """ Create the TuringEquityKnockoutOption by specifying the expiry date,
        strike price, option type, knockout level, coupon rate, coupon annualized flag,
        the number of observations per year, the notional and participation rate. """

        checkArgumentTypes(self.__init__, locals())

        if knock_out_type not in TuringKnockOutTypes:
            raise TuringError("Option Type " + str(knock_out_type) + " unknown.")

        self._expiry_date = expiry_date
        self._strike_price = strike_price
        self._knock_out_type = knock_out_type
        self._barrier = barrier
        self._rebate = rebate
        self._coupon_annualized_flag = coupon_annualized_flag
        self._notional = notional
        self._participation_rate = participation_rate
        self._num_observations_per_year = num_observations_per_year

###############################################################################

    def value(self,
              value_date: TuringDate,
              stock_price: float,
              discount_curve: TuringDiscountCurve,
              dividend_curve: TuringDiscountCurve,
              model: TuringModel,
              process_type: TuringProcessTypes = TuringProcessTypes.GBM,
              scheme: (TuringGBMNumericalScheme, TuringHestonNumericalScheme) = TuringGBMNumericalScheme.ANTITHETIC,
              num_ann_obs: int = 252,
              num_paths: int = 10000,
              seed: int = 4242):
        """ A Monte-Carlo based valuation of the knock out option which simulates
        the evolution of the stock price of at a specified number of annual
        observation times until expiry to examine if the barrier has been
        crossed and the corresponding value of the final payoff, if any. It
        assumes a GBM model for the stock price. """

        texp = (self._expiry_date - value_date) / gDaysInYear
        K = self._strike_price
        B = self._barrier
        knock_out_type = self._knock_out_type

        s0 = stock_price
        process = TuringProcessSimulator()

        r = discount_curve.ccRate(self._expiry_date)
        q = dividend_curve.ccRate(self._expiry_date)
        vol = model._volatility

        model_params = (stock_price, r-q, vol, scheme)
        #######################################################################
        if self._coupon_annualized_flag:
            if knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_CALL and stock_price <= B:
                return self._rebate * texp * self._notional * np.exp(- r * texp)
            elif knock_out_type == TuringKnockOutTypes.UP_AND_OUT_CALL and stock_price >= B:
                return self._rebate * texp * self._notional * np.exp(- r * texp)
            elif knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_PUT and stock_price <= B:
                return self._rebate * texp * self._notional * np.exp(- r * texp)
            elif knock_out_type == TuringKnockOutTypes.UP_AND_OUT_PUT and stock_price >= B:
                return self._rebate * texp * self._notional * np.exp(- r * texp)

        elif not self._coupon_annualized_flag:
            if knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_CALL and stock_price <= B:
                return self._rebate * self._notional * np.exp(- r * texp)
            elif knock_out_type == TuringKnockOutTypes.UP_AND_OUT_CALL and stock_price >= B:
                return self._rebate * self._notional * np.exp(- r * texp)
            elif knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_PUT and stock_price <= B:
                return self._rebate * self._notional * np.exp(- r * texp)
            elif knock_out_type == TuringKnockOutTypes.UP_AND_OUT_PUT and stock_price >= B:
                return self._rebate * self._notional * np.exp(- r * texp)

        #######################################################################

        # Get full set of paths
        Sall = process.getProcess(process_type, texp, model_params, num_ann_obs,
                                  num_paths, seed)

        (num_paths, _) = Sall.shape

        if knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_CALL or \
           knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_PUT:

            barrierCrossedFromAbove = [False] * num_paths

            for p in range(0, num_paths):
                barrierCrossedFromAbove[p] = np.any(Sall[p] <= B)

        if knock_out_type == TuringKnockOutTypes.UP_AND_OUT_CALL or \
           knock_out_type == TuringKnockOutTypes.UP_AND_OUT_PUT:

            barrierCrossedFromBelow = [False] * num_paths
            for p in range(0, num_paths):
                barrierCrossedFromBelow[p] = np.any(Sall[p] >= B)

        payoff = np.zeros(num_paths)
        ones = np.ones(num_paths)

        if self._coupon_annualized_flag:
            if knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_CALL:
                payoff = np.maximum((Sall[:, -1] - K) / s0, 0.0) * \
                    self._participation_rate * (ones - barrierCrossedFromAbove) + \
                        self._rebate * texp * (ones * barrierCrossedFromAbove)
            elif knock_out_type == TuringKnockOutTypes.UP_AND_OUT_CALL:
                payoff = np.maximum((Sall[:, -1] - K) / s0, 0.0) * \
                    self._participation_rate * (ones - barrierCrossedFromBelow) + \
                        self._rebate * texp * (ones * barrierCrossedFromBelow)
            elif knock_out_type == TuringKnockOutTypes.UP_AND_OUT_PUT:
                payoff = np.maximum((K - Sall[:, -1]) / s0, 0.0) * \
                    self._participation_rate * (ones - barrierCrossedFromBelow) + \
                        self._rebate * texp * (ones * barrierCrossedFromBelow)
            elif knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_PUT:
                payoff = np.maximum((K - Sall[:, -1]) / s0, 0.0) * \
                    self._participation_rate * (ones - barrierCrossedFromAbove) + \
                        self._rebate * texp * (ones * barrierCrossedFromAbove)
        elif not self._coupon_annualized_flag:
            if knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_CALL:
                payoff = np.maximum((Sall[:, -1] - K) / s0, 0.0) * \
                    self._participation_rate * (ones - barrierCrossedFromAbove) + \
                        self._rebate * (ones * barrierCrossedFromAbove)
            elif knock_out_type == TuringKnockOutTypes.UP_AND_OUT_CALL:
                payoff = np.maximum((Sall[:, -1] - K) / s0, 0.0) * \
                    self._participation_rate * (ones - barrierCrossedFromBelow) + \
                        self._rebate * (ones * barrierCrossedFromBelow)
            elif knock_out_type == TuringKnockOutTypes.UP_AND_OUT_PUT:
                payoff = np.maximum((K - Sall[:, -1]) / s0, 0.0) * \
                    self._participation_rate * (ones - barrierCrossedFromBelow) + \
                        self._rebate * (ones * barrierCrossedFromBelow)
            elif knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_PUT:
                payoff = np.maximum((K - Sall[:, -1]) / s0, 0.0) * \
                    self._participation_rate * (ones - barrierCrossedFromAbove) + \
                        self._rebate * (ones * barrierCrossedFromAbove)

        v = payoff.mean() * np.exp(- r * texp)

        return v * self._notional

###############################################################################

    def __repr__(self):
        s = to_string("OBJECT TYPE", type(self).__name__)
        s += to_string("EXPIRY DATE", self._expiry_date)
        s += to_string("STRIKE PRICE", self._strike_price)
        s += to_string("OPTION TYPE", self._knock_out_type)
        s += to_string("KNOCKOUT LEVEL", self._barrier)
        s += to_string("NUM OBSERVATIONS", self._num_observations_per_year)
        s += to_string("NOTIONAL", self._notional, "")
        return s

###############################################################################

    def _print(self):
        ''' Simple print function for backward compatibility. '''
        print(self)

###############################################################################
