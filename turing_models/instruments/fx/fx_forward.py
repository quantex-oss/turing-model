import datetime
from abc import ABCMeta
from dataclasses import dataclass
from enum import Enum
###############################################################################
# ALL CCY RATES MUST BE IN NUM UNITS OF DOMESTIC PER UNIT OF FOREIGN CURRENCY
# SO EURUSD = 1.30 MEANS 1.30 DOLLARS PER EURO SO DOLLAR IS THE DOMESTIC AND
# EUR IS THE FOREIGN CURRENCY
###############################################################################
from functools import cached_property

import numpy as np
import math
import pandas as pd
import QuantLib as ql

from fundamental.turing_db.data import Turing, TuringDB
from turing_models.instruments.common import greek, FX, Currency, CurrencyPair, DiscountCurveType
from turing_models.instruments.core import InstrumentBase
from turing_models.market.curves.curve_generation import DomDiscountCurveGen, ForDiscountCurveGen, FXForwardCurveGen
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.market.volatility.vol_surface_generation import FXVolSurfaceGen
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.models.model_volatility_fns import TuringVolFunctionTypes
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import TuringOptionTypes, TuringOptionType, TuringExerciseType
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.helper_functions import to_string
from turing_models.utilities.turing_date import TuringDate

error_str = "Time to expiry must be positive."
error_str3 = "Exchange Rate must be greater than zero."

@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class FXForward(FX, InstrumentBase, metaclass=ABCMeta):
    asset_id: str = None
    product_type: str = None  # FORWARD
    underlier: str = None
    underlier_symbol: (str, CurrencyPair) = None  # USD/CNY (外币/本币)
    notional: float = None
    notional_currency: (str, Currency) = None
    strike: float = None
    expiry: TuringDate = None
    start_date: TuringDate = None
    d_ccy_discount: float = None
    # 1 unit of foreign in domestic
    spot_days: int = 0
    value_date: TuringDate = TuringDate(
        *(datetime.date.today().timetuple()[:3]))
    _value_date = None
    _exchange_rate = None
    _domestic_discount_curve = None
    _foreign_discount_curve = None

    daycount = ql.Actual365Fixed()

    def __post_init__(self):
        super().__init__()
        self.check_underlier()
        if self.expiry:
            self.expiry_ql = ql.Date(self.expiry._d, self.expiry._m, self.expiry._y)
        self.domestic_name = None
        self.foreign_name = None
        self.notional_dom = None
        self.notional_for = None
        if self.expiry:
            self.final_delivery = self.expiry.addWeekDays(self.spot_days)
            if self.final_delivery < self.expiry:
                raise TuringError(
                    "Final delivery date must be on or after expiry.")

        if self.underlier_symbol:
            if isinstance(self.underlier_symbol, CurrencyPair):
                self.underlier_symbol = self.underlier_symbol.value
            elif isinstance(self.underlier_symbol, str):
                if len(self.underlier_symbol) != 7:
                    raise TuringError(
                        "Currency pair must be in ***/***format.")
            else:
                raise TuringError('Please check the input of underlier_symbol')

            self.foreign_name = self.underlier_symbol[0:3]
            self.domestic_name = self.underlier_symbol[4:7]

        if self.strike and np.any(self.strike < 0.0):
            raise TuringError("Negative strike.")

        if self.notional_currency and isinstance(self.notional_currency, Currency):
            self.notional_currency = self.notional_currency.value

        if self.domestic_name and self.foreign_name and self.notional_currency and \
                self.notional_currency != self.domestic_name and self.notional_currency != self.foreign_name:
            raise TuringError("Notional currency not in currency pair.")

        if self.notional_currency and self.domestic_name and self.foreign_name and self.notional and self.strike:
            if self.notional_currency == self.domestic_name:
                self.notional_dom = self.notional
                self.notional_for = self.notional / self.strike
            elif self.notional_currency == self.foreign_name:
                self.notional_for = self.notional
                self.notional_dom = self.notional * self.strike
            else:
                raise TuringError("Invalid notional currency.")

    @property
    def value_date_interface(self):
        date = self.ctx_pricing_date or self.value_date
        return date if date >= self.start_date else self.start_date

    @property
    def value_date_(self):
        date = self._value_date or self.value_date_interface
        return date if date >= self.start_date else self.start_date

    @value_date_.setter
    def value_date_(self, value: TuringDate):
        self._value_date = value

    @cached_property
    def get_exchange_rate(self):
        return TuringDB.exchange_rate(symbol=self.underlier_symbol, date=self.value_date_interface)[self.underlier_symbol]

    @property
    def exchange_rate(self):
        return self._exchange_rate or self.ctx_spot or self.get_exchange_rate

    @exchange_rate.setter
    def exchange_rate(self, value: float):
        self._exchange_rate = value

    @cached_property
    def get_fx_swap_data(self):
        return TuringDB.swap_curve(symbol=self.underlier_symbol, date=self.value_date_interface)[self.underlier_symbol]

    @cached_property
    def gen_dom_discount(self):
        return DomDiscountCurveGen(value_date=self.value_date_,
                                   d_ccy_discount = self.d_ccy_discount,
                                   curve_type=DiscountCurveType.FlatForward_CICC).discount_curve

    @property
    def domestic_discount_curve(self):
        if self._domestic_discount_curve:
            return self._domestic_discount_curve
        else:
            return self.gen_dom_discount

    @domestic_discount_curve.setter
    def domestic_discount_curve(self, value: TuringDiscountCurve):
        self._domestic_discount_curve = value
    
    @property
    def fx_forward_curve(self):
       return self.gen_fx_forward_curve

    @cached_property
    def gen_fx_forward_curve(self):
        return FXForwardCurveGen(value_date=self.value_date_,
                                   exchange_rate=self.exchange_rate,
                                   fx_swap_tenors=self.get_fx_swap_data['tenor'],
                                   fx_swap_origin_tenors=self.get_fx_swap_data['origin_tenor'],
                                   fx_swap_quotes=self.get_fx_swap_data['swap_point']
                                   ).discount_curve

    @cached_property
    def gen_for_discount_curve(self):
        return ForDiscountCurveGen(value_date=self.value_date_,
                                   exchange_rate=self.exchange_rate,
                                   fx_swap_tenors=self.get_fx_swap_data['tenor'],
                                   fx_swap_origin_tenors=self.get_fx_swap_data['origin_tenor'],
                                   fx_swap_quotes=self.get_fx_swap_data['swap_point'],
                                   domestic_discount_curve = self.domestic_discount_curve,
                                   fx_forward_curve = self.fx_forward_curve,
                                   curve_type=DiscountCurveType.FX_Implied_CICC).discount_curve

    @property
    def foreign_discount_curve(self):
        if self._foreign_discount_curve:
            return self._foreign_discount_curve
        else:
            return self.gen_for_discount_curve

    @foreign_discount_curve.setter
    def foreign_discount_curve(self, value: TuringDiscountCurve):
        self._foreign_discount_curve = value

    @property
    def tdel(self):
        spot_date = self.value_date_.addWeekDays(self.spot_days)
        td = (self.final_delivery - spot_date) / gDaysInYear
        if td < 0.0:
            raise TuringError(error_str)
        td = np.maximum(td, 1e-10)
        return td

    @property
    def texp(self):
        return (self.expiry - self.value_date_) / gDaysInYear

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
                                   fx_swap_quotes=self.get_fx_swap_data['swap_point']
                                   ).discount_curve.discount(self.expiry_ql)


    def check_underlier(self):
        if self.underlier_symbol and not self.underlier:
            if isinstance(self.underlier_symbol, Enum):
                self.underlier = Turing.get_fx_symbol_to_id(
                    _id=self.underlier_symbol.value).get('asset_id')
            else:
                self.underlier = Turing.get_fx_symbol_to_id(
                    _id=self.underlier_symbol).get('asset_id')
        

    def price(self):
        ''' Calculate the value of an FX forward contract where the current
        FX rate is the spotFXRate. '''

       
        atm = self.forward()

        if self.notional_currency == self.foreign_name:
            v = (atm - self.strike)
            v = v * self.notional_for * self.df_d
        elif self.notional_currency == self.domestic_name:
            v = (atm - self.strike)
            v = v * self.notional_dom * self.df_d * atm

        self._cash_dom = v * self.notional_dom / self.strike
        self._cash_for = v * self.notional_for / self.exchange_rate
        
        return v

        # return {"price": v,
        #         "cash_dom": self._cash_dom,
        #         "cash_for": self._cash_for,
        #         "not_dom": self.notional_dom,
        #         "not_for": self.notional_for,
        #         "ccy_dom": self.domestic_name,
        #         "ccy_for": self.foreign_name}

###############################################################################
    def forward(self):
        ''' Calculate the FX Forward rate that makes the value of the FX
        contract equal to zero. '''
        
        S0 = self.exchange_rate
        df_fwd = self.df_fwd
        fwdFXRate = S0 / df_fwd
        return fwdFXRate

###############################################################################
    def fx_delta(self):
        """ Calculation of the FX option delta by bumping the spot FX rate by
        1 cent of its value. This gives the FX spot delta. For speed we prefer
        to use the analytical calculation of the derivative given below. """

        bump_local = 0.0001
        return greek(self, self.price, "exchange_rate", bump=bump_local) * bump_local
    
###############################################################################
    def fx_gamma(self):
        return 0

    def fx_vega(self):
        return 0

    def fx_theta(self):
        return 0

    def fx_vanna(self):
        return 0

    def fx_volga(self):
        return 0
    
###############################################################################


    def _print(self):
        ''' Simple print function for backward compatibility. '''
        print(self)

###############################################################################

    
    
    
    
    