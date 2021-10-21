from dataclasses import dataclass
from functools import cached_property

import numpy as np
from scipy import optimize
from scipy.stats import norm
import QuantLib as ql

from fundamental.turing_db.option_data import FxOptionApi
from turing_models.market.curves.curve_generation import FXForwardCurveGen
from turing_models.instruments.common import greek
from turing_models.instruments.fx.fx_option import FXOption
from turing_models.market.volatility.vol_surface_generation import FXVolSurfaceGen
from turing_models.models.model_volatility_fns import TuringVolFunctionTypes
from turing_models.models.model_black_scholes_analytical import bs_value, bs_delta
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.utilities.mathematics import N
from turing_models.utilities.mathematics import nprime


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
# ALL CCY RATES MUST BE IN NUM UNITS OF DOMESTIC PER UNIT OF FOREIGN CURRENCY
# SO EURUSD = 1.30 MEANS 1.30 DOLLARS PER EURO SO DOLLAR IS THE DOMESTIC AND
# EUR IS THE FOREIGN CURRENCY
###############################################################################


error_str = "Time to expiry must be positive."
error_str2 = "Volatility should not be negative."
error_str3 = "Spot FX Rate must be greater than zero."


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class FXVanillaOption(FXOption):
    """ This is a class for an FX Option trade. It permits the user to
    calculate the price of an FX Option trade which can be expressed in a
    number of ways depending on the investor or hedger's currency. It aslo
    allows the calculation of the option's delta in a number of forms as
    well as the various Greek risk sensitivies. """
    daycount = ql.Actual365Fixed()

    def __post_init__(self):
        super().__post_init__()
        if self.expiry:
            self.expiry_ql = ql.Date(self.expiry._d, self.expiry._m, self.expiry._y)

    @cached_property
    def volatility_surface(self):
        if self.underlier_symbol:
            return FXVolSurfaceGen(value_date=self.value_date_,
                                   currency_pair=self.underlier_symbol,
                                   exchange_rate=self.exchange_rate,
                                   domestic_discount_curve=self.domestic_discount_curve,
                                   foreign_discount_curve=self.foreign_discount_curve,
                                   tenors=self.get_fx_implied_vol_data["tenor"],
                                   origin_tenors=self.get_fx_implied_vol_data["origin_tenor"],
                                   atm_vols=self.get_fx_implied_vol_data["ATM"],
                                   butterfly_25delta_vols=self.get_fx_implied_vol_data["25D BF"],
                                   risk_reversal_25delta_vols=self.get_fx_implied_vol_data["25D RR"],
                                   butterfly_10delta_vols=self.get_fx_implied_vol_data["10D BF"],
                                   risk_reversal_10delta_vols=self.get_fx_implied_vol_data["10D RR"],
                                   fx_swap_tenors=self.get_fx_swap_data['tenor'],
                                   fx_swap_origin_tenors=self.get_fx_swap_data['origin_tenor'],
                                   fx_swap_quotes=self.get_fx_swap_data['swap_point'],
                                   shibor_tenors=self.get_shibor_data['tenor'],
                                   shibor_origin_tenors=self.get_shibor_data['origin_tenor'],
                                   shibor_rates=self.get_shibor_data['rate'],
                                   shibor_swap_tenors=self.get_shibor_swap_data['tenor'],
                                   shibor_swap_origin_tenors=self.get_shibor_swap_data['origin_tenor'],
                                   shibor_swap_rates=self.get_shibor_swap_data['average'],
                                   volatility_function_type=TuringVolFunctionTypes.CICC).volatility_surface

    @property
    def volatility_(self):
        if self._volatility:
            v = self._volatility
        elif self.ctx_volatility:
            v = self.ctx_volatility
        elif self.volatility:
            v = self.model._volatility
        else:
            v = self.volatility_surface.interp_vol(self.expiry_ql, self.strike)
        if np.all(v >= 0.0):
            v = np.maximum(v, 1e-10)
            return v
        else:
            raise TuringError(error_str2)

    @volatility_.setter
    def volatility_(self, value: float):
        self._volatility = value

    @property
    def rd(self):
        return self.domestic_discount_curve.zeroRate(self.expiry_ql, self.daycount, ql.Continuous).rate()

    @property
    def rf(self):
        return self.foreign_discount_curve.zeroRate(self.expiry_ql, self.daycount, ql.Continuous).rate()
    
    @property
    def df_d(self):
        return self.domestic_discount_curve.discount(self.expiry_ql)

    @property
    def df_f(self):
        return self.foreign_discount_curve.discount(self.expiry_ql)

    @cached_property
    def df_fwd(self):
        return FXForwardCurveGen(value_date=self.value_date_,
                                 exchange_rate=self.exchange_rate,
                                 fx_swap_tenors=self.get_fx_swap_data['tenor'],
                                 fx_swap_origin_tenors=self.get_fx_swap_data['origin_tenor'],
                                 fx_swap_quotes=self.get_fx_swap_data['swap_point']).discount_curve.discount(self.expiry_ql)

    def rate_domestic(self):
        return self.rd

    def rate_foreign(self):
        return self.rf

    def spot(self):
        return self.exchange_rate

    def price(self):
        """ This function calculates the value of the option using a specified
        model with the resulting value being in domestic i.e. ccy2 terms.
        Recall that Domestic = CCY2 and Foreign = CCY1 and FX rate is in
        price in domestic of one unit of foreign currency. """

        S0 = self.exchange_rate
        K = self.strike
        df_d = self.df_d
        v = self.volatility_
        texp = self.texp
        atm = self.atm() 
        option_type = self.option_type_
        notional_dom = self.notional_dom
        notional_for = self.notional_for
        premium_currency = self.premium_currency
        d1 = (np.log(atm / K) + 0.5 * v ** 2 * texp) / (v * np.sqrt(texp))
        d2 = (np.log(atm / self.strike) - 0.5 * v ** 2 * texp) / (v * np.sqrt(texp))
        df = df_d 

        if option_type == TuringOptionTypes.EUROPEAN_CALL:
            
            vdf = df * (atm*norm.cdf(d1) - K*norm.cdf(d2))

        elif option_type == TuringOptionTypes.EUROPEAN_PUT:

            vdf = df * (K*norm.cdf(-d2) - atm*norm.cdf(-d1))

        else:
            raise TuringError("Unknown option type")

        # The option value v is in domestic currency terms but the value of
        # the option may be quoted in either currency terms and so we calculate
        # these

        pips_dom = vdf
        pips_for = vdf / (S0 * K)

        cash_dom = vdf * notional_dom / K
        cash_for = vdf * notional_for / S0

        pct_dom = vdf / K
        pct_for = vdf / S0

        if premium_currency == self.foreign_name:
            return cash_for
        elif premium_currency == self.domestic_name:
            return cash_dom
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

    def atm(self):

        S0 = self.exchange_rate
        df_fwd = self.df_fwd
        atm = S0 / df_fwd
        return atm

    def fx_delta_bs(self):
        """ Calculation of the FX Option delta. There are several definitions
        of delta and so we are required to return a dictionary of values. The
        definitions can be found on Page 44 of Foreign Exchange Option Pricing
        by Iain Clark, published by Wiley Finance. """

        S0 = self.exchange_rate
        K = self.strike
        rd = self.rd
        rf = self.rf
        texp = self.texp
        tdel = self.tdel
        v = self.volatility_
        option_type = self.option_type_
        notional_dom = self.notional_dom
        vpctf = bs_value(S0, texp, K, rd, rf, v, option_type.value, tdel) / S0

        pips_spot_delta = bs_delta(
            S0, texp, K, rd, rf, v, option_type.value, tdel)
        pips_fwd_delta = pips_spot_delta * np.exp(rf * tdel)
        pct_spot_delta_prem_adj = pips_spot_delta - vpctf
        pct_fwd_delta_prem_adj = np.exp(rf * tdel) * (pips_spot_delta - vpctf)
        return pips_spot_delta
        # return pips_spot_delta * (notional_dom / S0)

        # return {"pips_spot_delta": pips_spot_delta,
        #         "pips_fwd_delta": pips_fwd_delta,
        #         "pct_spot_delta_prem_adj": pct_spot_delta_prem_adj,
        #         "pct_fwd_delta_prem_adj": pct_fwd_delta_prem_adj}

    def fx_delta(self):
        """ Calculation of the FX option delta by bumping the spot FX rate by
        1 cent of its value. This gives the FX spot delta. For speed we prefer
        to use the analytical calculation of the derivative given below. """

        bump_local = 0.0001
        return greek(self, self.price, "exchange_rate", bump=bump_local) * bump_local

    def fx_gamma(self):
        """ Calculation of the FX option gamma by bumping the spot FX rate by
        1 cent of its value. This gives the FX spot gamma. For speed we prefer
        to use the analytical calculation of the derivative given below. """

        bump_local = 0.0001
        return greek(self, self.price, "exchange_rate", bump=bump_local, order=2) * bump_local ** 2

    def fx_vega(self):
        """ Calculation of the FX option vega by bumping the spot FX volatility by
        1 cent of its value. This gives the FX spot vega. For speed we prefer
        to use the analytical calculation of the derivative given below. """

        bump_local = 0.01
        return greek(self, self.price, "volatility_", bump=bump_local) * bump_local

    def fx_vanna(self):
        """ Calculation of the FX option vanna by bumping the spot FX volatility by
        1 cent of its value. This gives the FX spot vanna. For speed we prefer
        to use the analytical calculation of the derivative given below. """

        bump_local = 0.01
        return greek(self, self.fx_delta, "volatility_", bump=bump_local) * bump_local
    
    def fx_volga(self):
        """ Calculation of the FX option volga by bumping the spot FX volatility by
        1 cent of its value. This gives the FX spot volga. For speed we prefer
        to use the analytical calculation of the derivative given below. """

        bump_local = 0.01
        return greek(self, self.price, "volatility_", bump=bump_local, order=2) * bump_local ** 2
    
    def fx_theta(self):
        """ Calculation of the FX option theta by bumping 1 day. This gives the FX spot theta. For speed we prefer
        to use the analytical calculation of the derivative given below. """

        value_date = self.value_date_
        calendar = ql.China(ql.China.IB)
        today = ql.Date(value_date._d, value_date._m, value_date._y)
        tmr = calendar.advance(today, ql.Period('1D'))
        day_diff = tmr - today
        return greek(self, self.price, "value_date_", bump=day_diff, cus_inc=(self.value_date_.addDays, day_diff)) * day_diff

    # def fx_rho_bump(self):
    #     """ Calculation of the FX option rho by bumping the domestic discount curve by
    #     1 cent of its value. This gives the FX spot rho. For speed we prefer
    #     to use the analytical calculation of the derivative given below. """
    #
    #     bump_local = 0.0001
    #     return greek(self, self.price, "domestic_discount_curve", bump=bump_local,
    #                  cus_inc=(self.domestic_discount_curve.bump, bump_local)) * bump_local
    #
    # def fx_phi_bump(self):
    #     """ Calculation of the FX option phi by bumping the foreign discount curve by
    #     1 cent of its value. This gives the FX spot phi. For speed we prefer
    #     to use the analytical calculation of the derivative given below. """
    #
    #     bump_local = 0.0001
    #     return greek(self, self.price, "foreign_discount_curve", bump=bump_local,
    #                  cus_inc=(self.foreign_discount_curve.bump, bump_local)) * bump_local

    def fx_gamma_f(self):
        """ This function calculates the FX Option Gamma using the spot delta. """

        S0 = self.exchange_rate
        K = self.strike
        texp = self.texp
        v = self.volatility_
        rd = self.rd
        rf = self.rf

        lnS0k = np.log(S0 / K)
        sqrtT = np.sqrt(texp)
        den = v * sqrtT
        mu = rd - rf
        v2 = v * v
        d1 = (lnS0k + (mu + v2 / 2.0) * texp) / den
        gamma = np.exp(-rf * texp) * nprime(d1)
        gamma = gamma / S0 / den
        notional_dom = self.notional_dom

        return gamma

    def fx_vega_f(self):
        """ This function calculates the FX Option Vega using the spot delta. """

        S0 = self.exchange_rate
        K = self.strike
        texp = self.texp
        v = self.volatility_
        rd = self.rd
        rf = self.rf

        lnS0k = np.log(S0 / K)
        sqrtT = np.sqrt(texp)
        den = v * sqrtT
        mu = rd - rf
        v2 = v * v
        d1 = (lnS0k + (mu + v2 / 2.0) * texp) / den
        vega = S0 * sqrtT * np.exp(-rf * texp) * nprime(d1)
        notional_dom = self.notional_dom

        return vega

    def fx_theta_f(self):
        """ This function calculates the time decay of the FX option. """

        S0 = self.exchange_rate
        K = self.strike
        texp = self.texp
        v = self.volatility_
        option_type = self.option_type_
        rd = self.rd
        rf = self.rf

        lnS0k = np.log(S0 / K)
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

        notional_dom = self.notional_dom

        return v

    def fx_vanna_f(self):
        """ This function calculates the FX Option Vanna using the spot delta. """

        S0 = self.exchange_rate
        K = self.strike
        texp = self.texp
        v = self.volatility_
        rd = self.rd
        rf = self.rf

        lnS0k = np.log(S0 / K)
        sqrtT = np.sqrt(texp)
        den = v * sqrtT
        mu = rd - rf
        v2 = v * v
        d1 = (lnS0k + (mu + v2 / 2.0) * texp) / den
        d2 = (lnS0k + (mu - v2 / 2.0) * texp) / den
        vanna = - np.exp(-rf * texp) * d2 / v * nprime(d1)
        notional_dom = self.notional_dom

        return vanna

    def fx_volga_f(self):
        """ This function calculates the FX Option Vanna using the spot delta. """

        S0 = self.exchange_rate
        K = self.strike
        texp = self.texp
        v = self.volatility_
        rd = self.rd
        rf = self.rf

        lnS0k = np.log(S0 / K)
        sqrtT = np.sqrt(texp)
        den = v * sqrtT
        mu = rd - rf
        v2 = v * v
        d1 = (lnS0k + (mu + v2 / 2.0) * texp) / den
        d2 = (lnS0k + (mu - v2 / 2.0) * texp) / den
        volga = S0 * np.exp(-rf * texp) * sqrtT * d1 * d2 / v * nprime(d1)

        notional_dom = self.notional_dom

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

    def price_mc(self):
        """ Calculate the value of an FX Option using Monte Carlo methods.
        This function can be used to validate the risk measures calculated
        above or used as the starting code for a model exotic FX product that
        cannot be priced analytically. This function uses Numpy vectorisation
        for speed of execution."""

        v = self.volatility_
        K = self.strike
        spot_fx_rate = self.exchange_rate
        option_type = self.option_type_

        np.random.seed(self.seed)
        texp = self.texp
        tdel = self.tdel

        rd = self.rd
        rf = self.rf

        mu = rd - rf
        v2 = v ** 2
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

    def set_property_list(self, curve, underlier, _property, key):
        _list = []
        for k, v in curve.items():
            if k == underlier:
                for cu in v.get('iuir_curve_data'):
                    _list.append(cu.get(key))
        setattr(self, _property, _list)
        return _list

    def spot_path(self):
        return 'turing_models.instruments.fx.fx.ForeignExchange'

    def _resolve(self):
        if self.asset_id and not self.asset_id.startswith("OPTION_"):
            temp_dict = FxOptionApi.fetch_fx_option(
                gurl=None, asset_id=self.asset_id)
            for k, v in temp_dict.items():
                if not getattr(self, k, None) and v:
                    setattr(self, k, v)
        self.resolve_param()

    def resolve_param(self):
        self.check_underlier()
        # if self.underlier:
        #     if not self.exchange_rate:
        #         ex_rate = FxApi.get_exchange_rate(gurl=None,
        #                                           underlier=self.underlier)
        #         if ex_rate:
        #             setattr(self, "exchange_rate", ex_rate)
        #     if not self.tenors:
        #         FxOptionApi.get_iuir_curve(self)
        #     if not self.volatility:
        #         FxOptionApi.get_fx_volatility(self=self, gurl=None,
        #                                       volatility_types=["ATM", "25D BF", "25D RR", "10D BF", "10D RR"])

        if not self.product_type:
            setattr(self, 'product_type', 'VANILLA')
        self.__post_init__()
