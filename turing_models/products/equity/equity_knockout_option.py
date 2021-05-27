import numpy as np
from enum import Enum

from turing_models.utilities.error import TuringError
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.products.equity.equity_option import TuringEquityOption
from turing_models.models.process_simulator import TuringProcessSimulator, TuringProcessTypes, \
     TuringGBMNumericalScheme, TuringHestonNumericalScheme
from turing_models.models.model_black_scholes import TuringModel
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.utilities.helper_functions import labelToString, checkArgumentTypes
from turing_models.utilities.turing_date import TuringDate


###############################################################################


class TuringEquityKnockoutTypes(Enum):
    DOWN_AND_OUT_CALL = 1
    UP_AND_OUT_CALL = 2
    UP_AND_OUT_PUT = 3
    DOWN_AND_OUT_PUT = 4

###############################################################################


class TuringEquityKnockoutOption(TuringEquityOption):
    ''' Class to hold details of an Equity Knockout Option. '''

    def __init__(self,
                 expiry_date: TuringDate,
                 strike_price: float,
                 option_type: TuringEquityKnockoutTypes,
                 knock_out_level: float,
                 coupon_rate: float,
                 coupon_annualized_flag: bool = True,
                 num_observations_per_year: int = 252,
                 notional: float = 1.0,
                 participation_rate: float = 1.0):
        """ Create the TuringEquityKnockoutOption by specifying the expiry date,
        strike price, option type, knockout level, coupon rate, coupon annualized flag,
        the number of observations per year, the notional and participation rate. """

        checkArgumentTypes(self.__init__, locals())

        if option_type not in TuringEquityKnockoutTypes:
            raise TuringError("Option Type " + str(option_type) + " unknown.")

        self._expiry_date = expiry_date
        self._strike_price = strike_price
        self._option_type = option_type
        self._knockout_level = knock_out_level
        self._coupon_rate = coupon_rate
        self._coupon_annualized_flag = coupon_annualized_flag
        self._num_observations_per_year = num_observations_per_year
        self._notional = notional
        self._participation_rate = participation_rate

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
        B = self._knockout_level
        option_type = self._option_type

        s0 = stock_price
        process = TuringProcessSimulator()

        r = discount_curve.ccRate(self._expiry_date)
        q = dividend_curve.ccRate(self._expiry_date)
        vol = model._volatility

        model_params = (stock_price, r-q, vol, scheme)
        #######################################################################
        if self._coupon_annualized_flag:
            if option_type == TuringEquityKnockoutTypes.DOWN_AND_OUT_CALL and stock_price <= B:
                return self._coupon_rate * texp * self._notional * np.exp(- r * texp)
            elif option_type == TuringEquityKnockoutTypes.UP_AND_OUT_CALL and stock_price >= B:
                return self._coupon_rate * texp * self._notional * np.exp(- r * texp)
            elif option_type == TuringEquityKnockoutTypes.DOWN_AND_OUT_PUT and stock_price <= B:
                return self._coupon_rate * texp * self._notional * np.exp(- r * texp)
            elif option_type == TuringEquityKnockoutTypes.UP_AND_OUT_PUT and stock_price >= B:
                return self._coupon_rate * texp * self._notional * np.exp(- r * texp)

        elif not self._coupon_annualized_flag:
            if option_type == TuringEquityKnockoutTypes.DOWN_AND_OUT_CALL and stock_price <= B:
                return self._coupon_rate * self._notional * np.exp(- r * texp)
            elif option_type == TuringEquityKnockoutTypes.UP_AND_OUT_CALL and stock_price >= B:
                return self._coupon_rate * self._notional * np.exp(- r * texp)
            elif option_type == TuringEquityKnockoutTypes.DOWN_AND_OUT_PUT and stock_price <= B:
                return self._coupon_rate * self._notional * np.exp(- r * texp)
            elif option_type == TuringEquityKnockoutTypes.UP_AND_OUT_PUT and stock_price >= B:
                return self._coupon_rate * self._notional * np.exp(- r * texp)

        #######################################################################

        # Get full set of paths
        Sall = process.getProcess(process_type, texp, model_params, num_ann_obs,
                                  num_paths, seed)

        (num_paths, _) = Sall.shape

        if option_type == TuringEquityKnockoutTypes.DOWN_AND_OUT_CALL or \
           option_type == TuringEquityKnockoutTypes.DOWN_AND_OUT_PUT:

            barrierCrossedFromAbove = [False] * num_paths

            for p in range(0, num_paths):
                barrierCrossedFromAbove[p] = np.any(Sall[p] <= B)

        if option_type == TuringEquityKnockoutTypes.UP_AND_OUT_CALL or \
           option_type == TuringEquityKnockoutTypes.UP_AND_OUT_PUT:

            barrierCrossedFromBelow = [False] * num_paths
            for p in range(0, num_paths):
                barrierCrossedFromBelow[p] = np.any(Sall[p] >= B)

        payoff = np.zeros(num_paths)
        ones = np.ones(num_paths)

        if self._coupon_annualized_flag:
            if option_type == TuringEquityKnockoutTypes.DOWN_AND_OUT_CALL:
                payoff = np.maximum((Sall[:, -1] - K) / s0, 0.0) * \
                    self._participation_rate * (ones - barrierCrossedFromAbove) + \
                        self._coupon_rate * texp * (ones * barrierCrossedFromAbove)
            elif option_type == TuringEquityKnockoutTypes.UP_AND_OUT_CALL:
                payoff = np.maximum((Sall[:, -1] - K) / s0, 0.0) * \
                    self._participation_rate * (ones - barrierCrossedFromBelow) + \
                        self._coupon_rate * texp * (ones * barrierCrossedFromBelow)
            elif option_type == TuringEquityKnockoutTypes.UP_AND_OUT_PUT:
                payoff = np.maximum((K - Sall[:, -1]) / s0, 0.0) * \
                    self._participation_rate * (ones - barrierCrossedFromBelow) + \
                        self._coupon_rate * texp * (ones * barrierCrossedFromBelow)
            elif option_type == TuringEquityKnockoutTypes.DOWN_AND_OUT_PUT:
                payoff = np.maximum((K - Sall[:, -1]) / s0, 0.0) * \
                    self._participation_rate * (ones - barrierCrossedFromAbove) + \
                        self._coupon_rate * texp * (ones * barrierCrossedFromAbove)
        elif not self._coupon_annualized_flag:
            if option_type == TuringEquityKnockoutTypes.DOWN_AND_OUT_CALL:
                payoff = np.maximum((Sall[:, -1] - K) / s0, 0.0) * \
                    self._participation_rate * (ones - barrierCrossedFromAbove) + \
                        self._coupon_rate * (ones * barrierCrossedFromAbove)
            elif option_type == TuringEquityKnockoutTypes.UP_AND_OUT_CALL:
                payoff = np.maximum((Sall[:, -1] - K) / s0, 0.0) * \
                    self._participation_rate * (ones - barrierCrossedFromBelow) + \
                        self._coupon_rate * (ones * barrierCrossedFromBelow)
            elif option_type == TuringEquityKnockoutTypes.UP_AND_OUT_PUT:
                payoff = np.maximum((K - Sall[:, -1]) / s0, 0.0) * \
                    self._participation_rate * (ones - barrierCrossedFromBelow) + \
                        self._coupon_rate * (ones * barrierCrossedFromBelow)
            elif option_type == TuringEquityKnockoutTypes.DOWN_AND_OUT_PUT:
                payoff = np.maximum((K - Sall[:, -1]) / s0, 0.0) * \
                    self._participation_rate * (ones - barrierCrossedFromAbove) + \
                        self._coupon_rate * (ones * barrierCrossedFromAbove)

        v = payoff.mean() * np.exp(- r * texp)

        return v * self._notional

###############################################################################

    def __repr__(self):
        s = labelToString("OBJECT TYPE", type(self).__name__)
        s += labelToString("EXPIRY DATE", self._expiry_date)
        s += labelToString("STRIKE PRICE", self._strike_price)
        s += labelToString("OPTION TYPE", self._option_type)
        s += labelToString("KNOCKOUT LEVEL", self._knockout_level)
        s += labelToString("NUM OBSERVATIONS", self._num_observations_per_year)
        s += labelToString("NOTIONAL", self._notional, "")
        return s

###############################################################################

    def _print(self):
        ''' Simple print function for backward compatibility. '''
        print(self)

###############################################################################
