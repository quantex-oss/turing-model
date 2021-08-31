import datetime
from dataclasses import dataclass

import numpy as np
from scipy import optimize
from numba import njit
from fundamental.market.curves.discount_curve_flat import TuringDiscountCurveFlat

from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.mathematics import nprime
from turing_models.utilities.global_variables import gDaysInYear, gSmall
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.products.fx.fx_mkt_conventions import TuringFXDeltaMethod
from turing_models.models.model_crr_tree import crrTreeValAvg
from turing_models.models.model_sabr import volFunctionSABR
from turing_models.models.model_sabr import TuringModelSABR
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.models.model_black_scholes_analytical import bs_value, bs_delta
from turing_models.utilities.helper_functions import checkArgumentTypes, to_string
from turing_models.utilities.mathematics import N

# Todo: vvprice, volquote


def f(volatility, *args):
    """ This is the objective function used in the determination of the FX
    Option implied volatility which is computed in the class below. """

    self = args[0]
    price = args[1]
    self.volatility = volatility
    vdf = self.price()
    objFn = vdf - price

    return objFn

###############################################################################


def f_vega(volatility, *args):
    """ This is the derivative of the objective function with respect to the
    option volatility. It is used to speed up the determination of the FX
    Option implied volatility which is computed in the class below. """

    self = args[0]
    self.volatility = volatility
    fprime = self.vega()

    return fprime

###############################################################################


@njit(fastmath=True, cache=True)
def fast_delta(s, t, k, rd, rf, vol, deltaTypeValue, optionTypeValue):
    """ Calculation of the FX Option delta. Used in the determination of
    the volatility surface. Avoids discount curve interpolation so it
    should be slightly faster than the full calculation of delta. """

    pips_spot_delta = bs_delta(s, t, k, rd, rf, vol, optionTypeValue)

    if deltaTypeValue == TuringFXDeltaMethod.SPOT_DELTA.value:
        return pips_spot_delta
    elif deltaTypeValue == TuringFXDeltaMethod.FORWARD_DELTA.value:
        pips_fwd_delta = pips_spot_delta * np.exp(rf*t)
        return pips_fwd_delta
    elif deltaTypeValue == TuringFXDeltaMethod.SPOT_DELTA_PREM_ADJ.value:
        vpctf = bs_value(s, t, k, rd, rf, vol, optionTypeValue) / s
        pct_spot_delta_prem_adj = pips_spot_delta - vpctf
        return pct_spot_delta_prem_adj
    elif deltaTypeValue == TuringFXDeltaMethod.FORWARD_DELTA_PREM_ADJ.value:
        vpctf = bs_value(s, t, k, rd, rf, vol, optionTypeValue) / s
        pct_fwd_delta_prem_adj = np.exp(rf*t) * (pips_spot_delta - vpctf)
        return pct_fwd_delta_prem_adj
    else:
        raise TuringError("Unknown TuringFXDeltaMethod")

###############################################################################
# ALL CCY RATES MUST BE IN NUM UNITS OF DOMESTIC PER UNIT OF FOREIGN CURRENCY
# SO EURUSD = 1.30 MEANS 1.30 DOLLARS PER EURO SO DOLLAR IS THE DOMESTIC AND
# EUR IS THE FOREIGN CURRENCY
###############################################################################


error_str = "Time to expiry must be positive."
error_str2 = "Volatility should not be negative."
error_str3 = "Spot FX Rate must be greater than zero."


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class FXVanillaOption():
    """ This is a class for an FX Option trade. It permits the user to
    calculate the price of an FX Option trade which can be expressed in a
    number of ways depending on the investor or hedger's currency. It aslo
    allows the calculation of the option's delta in a number of forms as
    well as the various Greek risk sensitivies. """

    trade_date: TuringDate = None
    maturity_date: TuringDate = None
    cut_off_date: TuringDate = None
    # 1 unit of foreign in domestic
    strike_fx_rate: (float, np.ndarray) = None
    currency_pair: str = None
    option_type: (TuringOptionTypes, list) = None
    notional: float = None
    premium_currency: str = None
    spot_days: int = 0
    value_date: TuringDate = TuringDate(
        *(datetime.date.today().timetuple()[:3]))
    spot_fx_rate: float = None  # 1 unit of foreign in domestic
    ccy1_cc_rate: float = None
    ccy2_cc_rate: float = None
    volatility: float = None
    market_price = None
    __value_date = None
    _spot_fx_rate = None

    def __post_init__(self):

        self.delivery_date = self.maturity_date.addWeekDays(self.spot_days)

        if self.delivery_date < self.maturity_date:
            raise TuringError(
                "Delivery date must be on or after maturity date.")

        if len(self.currency_pair) != 6:
            raise TuringError("Currency pair must be 6 characters.")

        if np.any(self.strike_fx_rate < 0.0):
            raise TuringError("Negative strike.")

        self.foreign_name = self.currency_pair[0:3]
        self.domestic_name = self.currency_pair[3:6]

        if self.premium_currency != self.domestic_name and self.premium_currency != self.foreign_name:
            raise TuringError("Premium currency not in currency pair.")

        if self.option_type != TuringOptionTypes.EUROPEAN_CALL and \
           self.option_type != TuringOptionTypes.EUROPEAN_PUT and\
           self.option_type != TuringOptionTypes.AMERICAN_CALL and \
           self.option_type != TuringOptionTypes.AMERICAN_PUT:
            raise TuringError("Unknown Option Type:" + self.option_type)

        if np.any(self.spot_fx_rate <= 0.0):
            raise TuringError(error_str3)

        self.num_paths = 100000
        self.seed = 4242

    @property
    def value_date_(self):
        date = self.__value_date or self.ctx.pricing_date or self._value_date
        return date if date >= self.trade_date else self.trade_date

    @value_date_.setter
    def value_date_(self, value: TuringDate):
        self.__value_date = value

    @property
    def foreign_discount_curve(self):
        return TuringDiscountCurveFlat(self.value_date, self.ccy1_cc_rate)

    @property
    def domestic_discount_curve(self):
        return TuringDiscountCurveFlat(self.value_date, self.ccy2_cc_rate)

    @property
    def model(self):
        return TuringModelBlackScholes(self.volatility)

    @property
    def tdel(self):
        spot_date = self.value_date.addWeekDays(self.spot_days)
        td = (self.delivery_date - spot_date) / gDaysInYear
        if td < 0.0:
            raise TuringError(error_str)
        td = np.maximum(td, 1e-10)
        return td

    @property
    def texp(self):
        return (self.cut_off_date - self.value_date) / gDaysInYear

    @property
    def rd(self):
        texp = self.texp
        domDF = self.domestic_discount_curve._df(texp)
        return -np.log(domDF) / texp

    @property
    def rf(self):
        texp = self.texp
        forDF = self.foreign_discount_curve._df(self.texp)
        return -np.log(forDF) / texp

    @property
    def vol(self):
        if isinstance(self.model, TuringModelBlackScholes):
            v = self.model._volatility
        elif isinstance(self.model, TuringModelSABR):
            F0T = self.spot_fx_rate * np.exp((self.rd - self.rf) * self.texp)
            v = volFunctionSABR(model.alpha,
                                model.beta,
                                model.rho,
                                model.nu,
                                F0T,
                                self.strike_fx_rate,
                                self.texp)

        if np.all(v >= 0.0):
            v = np.maximum(v, 1e-10)
            return v
        else:
            raise TuringError(error_str2)

    # @property
    # def spot_fx_rate_(self) -> float:
    #     s = self._spot_fx_rate or self.spot_fx_rate
    #     if np.all(s > 0.0):
    #         return s
    #     else:
    #         raise TuringError(error_str3)

    # @spot_fx_rate_.setter
    # def spot_fx_rate_(self, value: float):
    #     self._spot_fx_rate = value

    def price(self):
        """ This function calculates the value of the option using a specified
        model with the resulting value being in domestic i.e. ccy2 terms.
        Recall that Domestic = CCY2 and Foreign = CCY1 and FX rate is in
        price in domestic of one unit of foreign currency. """

        S0 = self.spot_fx_rate
        K = self.strike_fx_rate
        rd = self.rd
        rf = self.rf
        v = self.vol
        texp = self.texp
        tdel = self.tdel
        notional = self.notional
        premium_currency = self.premium_currency
        domestic_name = self.domestic_name
        foreign_name = self.foreign_name
        option_type = self.option_type

        if option_type == TuringOptionTypes.EUROPEAN_CALL:

            vdf = bs_value(S0, texp, K, rd, rf, v,
                           TuringOptionTypes.EUROPEAN_CALL.value, tdel)

        elif option_type == TuringOptionTypes.EUROPEAN_PUT:

            vdf = bs_value(S0, texp, K, rd, rf, v,
                           TuringOptionTypes.EUROPEAN_PUT.value, tdel)

        # elif option_type == TuringOptionTypes.AMERICAN_CALL:
        #     numStepsPerYear = 100
        #     vdf = crrTreeValAvg(S0, rd, rf, volatility, numStepsPerYear,
        #                         texp, TuringOptionTypes.AMERICAN_CALL.value, K)['value']
        # elif option_type == TuringOptionTypes.AMERICAN_PUT:
        #     numStepsPerYear = 100
        #     vdf = crrTreeValAvg(S0, rd, rf, volatility, numStepsPerYear,
        #                         texp, TuringOptionTypes.AMERICAN_PUT.value, K)['value']
        else:
            raise TuringError("Unknown option type")

        # The option value v is in domestic currency terms but the value of
        # the option may be quoted in either currency terms and so we calculate
        # these

        if premium_currency == domestic_name:
            notional_dom = notional
            notional_for = notional / K
        elif premium_currency == foreign_name:
            notional_dom = notional * K
            notional_for = notional
        else:
            raise TuringError("Invalid notional currency.")

        pips_dom = vdf
        pips_for = vdf / (S0 * K)

        cash_dom = vdf * notional_dom / K
        cash_for = vdf * notional_for / S0

        pct_dom = vdf / K
        pct_for = vdf / S0

        return vdf
        # return {'v': vdf,
        #         "cash_dom": cash_dom,
        #         "cash_for": cash_for,
        #         "pips_dom": pips_dom,
        #         "pips_for": pips_for,
        #         "pct_dom": pct_dom,
        #         "pct_for": pct_for,
        #         "not_dom": notional_dom,
        #         "not_for": notional_for,
        #         "ccy_dom": self.domestic_name,
        #         "ccy_for": self.foreign_name}

    def delta_bump(self):
        """ Calculation of the FX option delta by bumping the spot FX rate by
        1 cent of its value. This gives the FX spot delta. For speed we prefer
        to use the analytical calculation of the derivative given below. """

        bump_local = 0.0001 * self.spot_fx_rate

        return greek(self, self.price, "spot_fx_rate", bump=bump_local)

    def delta(self):
        """ Calculation of the FX Option delta. There are several definitions
        of delta and so we are required to return a dictionary of values. The
        definitions can be found on Page 44 of Foreign Exchange Option Pricing
        by Iain Clark, published by Wiley Finance. """

        S0 = self.spot_fx_rate
        K = self.strike_fx_rate
        rd = self.rd
        rf = self.rf
        texp = self.texp
        tdel = self.tdel
        v = self.vol
        option_type = self.option_type

        pips_spot_delta = bs_delta(
            S0, texp, K, rd, rf, v, option_type.value, tdel)
        pips_fwd_delta = pips_spot_delta * np.exp(rf * tdel)
        vpctf = bs_value(S0, texp, K, rd, rf, v, option_type.value, tdel) / S0
        pct_spot_delta_prem_adj = pips_spot_delta - vpctf
        pct_fwd_delta_prem_adj = np.exp(rf * tdel) * (pips_spot_delta - vpctf)

        return {"pips_spot_delta": pips_spot_delta,
                "pips_fwd_delta": pips_fwd_delta,
                "pct_spot_delta_prem_adj": pct_spot_delta_prem_adj,
                "pct_fwd_delta_prem_adj": pct_fwd_delta_prem_adj}

    def fast_delta(self):
        """ Calculation of the FX Option delta. Used in the determination of
        the volatility surface. Avoids discount curve interpolation so it
        should be slightly faster than the full calculation of delta. """

        S0 = self.spot_fx_rate
        K = self.strike_fx_rate
        rd = self.rd
        rf = self.rf
        texp = self.texp
        tdel = self.tdel
        v = self.vol
        option_type = self.option_type

        pips_spot_delta = bs_delta(
            S0, texp, K, rd, rf, v, option_type.value, tdel)
        pips_fwd_delta = pips_spot_delta * np.exp(rf * tdel)

        vpctf = bs_value(S0, texp, K, rd, rf, v, option_type.value, tdel) / S0

        pct_spot_delta_prem_adj = pips_spot_delta - vpctf
        pct_fwd_delta_prem_adj = np.exp(rf * tdel) * (pips_spot_delta - vpctf)

        return {"pips_spot_delta": pips_spot_delta,
                "pips_fwd_delta": pips_fwd_delta,
                "pct_spot_delta_prem_adj": pct_spot_delta_prem_adj,
                "pct_fwd_delta_prem_adj": pct_fwd_delta_prem_adj}

    def gamma(self):
        """ This function calculates the FX Option Gamma using the spot delta. """

        S0 = self.spot_fx_rate
        K = self.strike_fx_rate
        texp = self.texp
        v = self.vol

        domDf = self.domestic_discount_curve._df(texp)
        rd = -np.log(domDf) / texp

        forDf = self.foreign_discount_curve._df(texp)
        rf = -np.log(forDf) / texp

        lnS0k = np.log(S0 / K)
        sqrtT = np.sqrt(texp)
        den = v * sqrtT
        mu = rd - rf
        v2 = v * v
        d1 = (lnS0k + (mu + v2 / 2.0) * texp) / den
        gamma = np.exp(-rf * texp) * nprime(d1)
        gamma = gamma / S0 / den

        return gamma

    def vega(self):
        """ This function calculates the FX Option Vega using the spot delta. """

        S0 = self.spot_fx_rate
        K = self.strike_fx_rate
        texp = self.texp
        v = self.vol

        domDf = self.domestic_discount_curve._df(texp)
        rd = -np.log(domDf) / texp

        forDf = self.foreign_discount_curve._df(texp)
        rf = -np.log(forDf) / texp

        lnS0k = np.log(S0 / K)
        sqrtT = np.sqrt(texp)
        den = v * sqrtT
        mu = rd - rf
        v2 = v * v
        d1 = (lnS0k + (mu + v2 / 2.0) * texp) / den
        vega = S0 * sqrtT * np.exp(-rf * texp) * nprime(d1)

        return vega

    def theta(self):
        """ This function calculates the time decay of the FX option. """

        S0 = self.spot_fx_rate
        K = self.strike_fx_rate
        texp = self.texp
        v = self.vol
        option_type = self.option_type

        domDf = self.domestic_discount_curve._df(texp)
        rd = -np.log(domDf)/texp

        forDf = self.foreign_discount_curve._df(texp)
        rf = -np.log(forDf)/texp

        lnS0k = np.log(S0/K)
        sqrtT = np.sqrt(texp)
        den = v * sqrtT
        mu = rd - rf
        v2 = v * v
        d1 = (lnS0k + (mu + v2 / 2.0) * texp) / den
        d2 = (lnS0k + (mu - v2 / 2.0) * texp) / den

        if option_type == TuringOptionTypes.EUROPEAN_CALL:
            v = - S0 * np.exp(-rf * texp) * nprime(d1) * v / 2.0 / sqrtT
            v = v + rf * S0 * np.exp(-rf * texp) * N(d1)
            v = v - rd * K * np.exp(-rd * texp) * N(d2)
        elif option_type == TuringOptionTypes.EUROPEAN_PUT:
            v = - S0 * np.exp(-rf * texp) * nprime(d1) * v / 2.0 / sqrtT
            v = v + rd * K * np.exp(-rd * texp) * N(-d2)
            v = v - rf * S0 * np.exp(-rf * texp) * N(-d1)
        else:
            raise TuringError("Unknown option type")

        return v

    def vanna(self):
        """ This function calculates the FX Option Vanna using the spot delta. """

        S0 = self.spot_fx_rate
        K = self.strike_fx_rate
        texp = self.texp
        v = self.vol

        domDf = self.domestic_discount_curve._df(texp)
        rd = -np.log(domDf) / texp

        forDf = self.foreign_discount_curve._df(texp)
        rf = -np.log(forDf) / texp

        lnS0k = np.log(S0 / K)
        sqrtT = np.sqrt(texp)
        den = v * sqrtT
        mu = rd - rf
        v2 = v * v
        d1 = (lnS0k + (mu + v2 / 2.0) * texp) / den
        d2 = (lnS0k + (mu - v2 / 2.0) * texp) / den
        vanna = - np.exp(-rf * texp) * d2 / v * nprime(d1)

        return vanna

    def volga(self):
        """ This function calculates the FX Option Vanna using the spot delta. """

        S0 = self.spot_fx_rate
        K = self.strike_fx_rate
        texp = self.texp
        v = self.vol

        domDf = self.domestic_discount_curve._df(texp)
        rd = -np.log(domDf) / texp

        forDf = self.foreign_discount_curve._df(texp)
        rf = -np.log(forDf) / texp

        lnS0k = np.log(S0 / K)
        sqrtT = np.sqrt(texp)
        den = v * sqrtT
        mu = rd - rf
        v2 = v * v
        d1 = (lnS0k + (mu + v2 / 2.0) * texp) / den
        d2 = (lnS0k + (mu - v2 / 2.0) * texp) / den
        volga = S0 * np.exp(-rf * texp) * sqrtT * d1 * d2 / v * nprime(d1)

        return volga

    def implied_volatility(self):
        """ This function determines the implied volatility of an FX option
        given a price and the other option details. It uses a one-dimensional
        Newton root search algorith to determine the implied volatility. """

        argtuple = (self, self.market_price)
        v = self.volatility
        sigma = optimize.newton(f, x0=0.2, fprime=f_vega, args=argtuple,
                                tol=1e-6, maxiter=50, fprime2=None)
        self.volatility = v
        return sigma

###############################################################################

    def price_mc(self):
        """ Calculate the value of an FX Option using Monte Carlo methods.
        This function can be used to validate the risk measures calculated
        above or used as the starting code for a model exotic FX product that
        cannot be priced analytically. This function uses Numpy vectorisation
        for speed of execution."""

        v = self.vol
        K = self.strike_fx_rate
        spot_fx_rate = self.spot_fx_rate
        option_type = self.option_type

        np.random.seed(self.seed)
        texp = self.texp
        tdel = self.tdel

        domDF = self.domestic_discount_curve.df(self.delivery_date)
        forDF = self.foreign_discount_curve.df(self.delivery_date)

        rd = -np.log(domDF)/tdel
        rf = -np.log(forDF)/tdel

        mu = rd - rf
        v2 = v**2
        sqrtdt = np.sqrt(texp)

        # Use Antithetic variables
        g = np.random.normal(0.0, 1.0, size=(1, self.num_paths))
        s = spot_fx_rate * np.exp((mu - v2 / 2.0) * texp)
        m = np.exp(g * sqrtdt * v)
        s_1 = s * m
        s_2 = s / m

        if option_type == TuringOptionTypes.EUROPEAN_CALL:
            payoff_a_1 = np.maximum(s_1 - K, 0.0)
            payoff_a_2 = np.maximum(s_2 - K, 0.0)
        elif option_type == TuringOptionTypes.EUROPEAN_PUT:
            payoff_a_1 = np.maximum(K - s_1, 0.0)
            payoff_a_2 = np.maximum(K - s_2, 0.0)
        else:
            raise TuringError("Unknown option type.")

        payoff = np.mean(payoff_a_1) + np.mean(payoff_a_2)
        v = payoff * np.exp(-rd * tdel) / 2.0
        return v

###############################################################################

    def __repr__(self):
        s = to_string("OBJECT TYPE", type(self).__name__)
        s += to_string("EXPIRY DATE", self.expiry_date)
        s += to_string("CURRENCY PAIR", self.currency_pair)
        s += to_string("PREMIUM CCY", self.premium_currency)
        s += to_string("STRIKE FX RATE", self.strike_fx_rate)
        s += to_string("OPTION TYPE", self.option_type)
        s += to_string("SPOT DAYS", self.spot_days)
        s += to_string("NOTIONAL", self.notional, "")
        return s

###############################################################################

    def _print(self):
        """ Simple print function for backward compatibility. """
        print(self)

###############################################################################
