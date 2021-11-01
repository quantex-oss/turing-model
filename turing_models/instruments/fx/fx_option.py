###############################################################################
# ALL CCY RATES MUST BE IN NUM UNITS OF DOMESTIC PER UNIT OF FOREIGN CURRENCY
# SO EURUSD = 1.30 MEANS 1.30 DOLLARS PER EURO SO DOLLAR IS THE DOMESTIC AND
# EUR IS THE FOREIGN CURRENCY
###############################################################################
import datetime
from abc import ABCMeta
from dataclasses import dataclass
from enum import Enum

import numpy as np
import QuantLib as ql

from fundamental.turing_db.data import Turing, TuringDB
from turing_models.instruments.common import FX, Currency, CurrencyPair, DiscountCurveType
from turing_models.instruments.core import InstrumentBase
from turing_models.market.curves.curve_generation import DomDiscountCurveGen, ForDiscountCurveGen, FXForwardCurveGen
from turing_models.market.volatility.vol_surface_generation import FXVolSurfaceGen
from turing_models.models.model_volatility_fns import TuringVolFunctionTypes
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import TuringOptionType, TuringExerciseType
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.helper_functions import to_string
from turing_models.utilities.turing_date import TuringDate


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class FXOption(FX, InstrumentBase, metaclass=ABCMeta):
    asset_id: str = None
    product_type: str = None  # VANILLA/Digital
    underlier: str = None
    underlier_symbol: (str, CurrencyPair) = None  # USD/CNY (外币/本币)
    notional: float = None
    notional_currency: (str, Currency) = None
    strike: float = None
    expiry: TuringDate = None
    cut_off_time: TuringDate = None
    exercise_type: (
        str, TuringExerciseType) = TuringExerciseType.EUROPEAN  # EUROPEAN
    option_type: (str, TuringOptionType) = None  # CALL/PUT
    start_date: TuringDate = None
    # 1 unit of foreign in domestic
    premium_currency: (str, Currency) = None
    # spot_days: int = 0
    value_date: TuringDate = TuringDate(
        *(datetime.date.today().timetuple()[:3]))
    volatility: float = None
    market_price = None
    _value_date = None
    _exchange_rate = None
    _volatility = None
    _domestic_discount_curve = None
    _foreign_discount_curve = None

    def __post_init__(self):
        super().__init__()
        self.check_underlier()
        self.domestic_name = None
        self.foreign_name = None
        self.notional_dom = None
        self.notional_for = None
        if self.expiry:
            self.expiry_ql = ql.Date(self.expiry._d, self.expiry._m, self.expiry._y)
            # self.final_delivery = self.expiry.addWeekDays(self.spot_days)
            # if self.final_delivery < self.expiry:
            #     raise TuringError(
            #         "Final delivery date must be on or after expiry.")

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
        
        if not self.notional_currency and self.underlier_symbol:
            self.notional_currency = self.foreign_name

        if self.notional_currency and isinstance(self.notional_currency, Currency):
            self.notional_currency = self.notional_currency.value

        if self.premium_currency and isinstance(self.premium_currency, Currency):
            self.premium_currency = self.premium_currency.value

        if self.domestic_name and self.foreign_name and self.premium_currency and \
                self.premium_currency != self.domestic_name and self.premium_currency != self.foreign_name:
            raise TuringError("Premium currency not in currency pair.")

        if self.notional_currency and self.domestic_name and self.foreign_name and self.notional and self.strike:
            if self.notional_currency == self.domestic_name:
                self.notional_dom = self.notional
                self.notional_for = self.notional / self.strike
            elif self.notional_currency == self.foreign_name:
                self.notional_for = self.notional
                self.notional_dom = self.notional * self.strike
            else:
                raise TuringError("Invalid notional currency.")

        if not self.cut_off_time or not isinstance(self.cut_off_time, TuringDate):
            self.cut_off_time = self.expiry

        self.daycount = ql.Actual365Fixed()
        self.num_paths = 100000
        self.seed = 4242

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

    @property
    def get_exchange_rate(self):
        return TuringDB.exchange_rate(symbol=self.underlier_symbol, date=self.value_date_interface)[self.underlier_symbol]

    @property
    def exchange_rate(self):
        return self._exchange_rate or self.ctx_spot or self.get_exchange_rate

    @exchange_rate.setter
    def exchange_rate(self, value: float):
        self._exchange_rate = value

    @property
    def get_shibor_data(self):
        return TuringDB.shibor_curve(date=self.value_date_interface)

    @property
    def get_shibor_swap_data(self):
        return TuringDB.irs_curve(curve_type='Shibor3M', date=self.value_date_interface)['Shibor3M']

    @property
    def get_fx_swap_data(self):
        return TuringDB.swap_curve(symbol=self.underlier_symbol, date=self.value_date_interface)[self.underlier_symbol]

    @property
    def get_fx_implied_vol_data(self):
        return TuringDB.fx_implied_volatility_curve(symbol=self.underlier_symbol,
                                                    volatility_type=["ATM", "25D BF", "25D RR", "10D BF", "10D RR"],
                                                    date=self.value_date_interface)[self.underlier_symbol]

    @property
    def gen_dom_discount(self):
        return DomDiscountCurveGen(value_date=self.value_date_,
                                   shibor_tenors=self.get_shibor_data['tenor'],
                                   shibor_origin_tenors=self.get_shibor_data['origin_tenor'],
                                   shibor_rates=self.get_shibor_data['rate'],
                                   shibor_swap_tenors=self.get_shibor_swap_data['tenor'],
                                   shibor_swap_origin_tenors=self.get_shibor_swap_data['origin_tenor'],
                                   shibor_swap_rates=self.get_shibor_swap_data['average'],
                                   curve_type=DiscountCurveType.Shibor3M).discount_curve

    @property
    def domestic_discount_curve(self):
        if self._domestic_discount_curve:
            return self._domestic_discount_curve
        else:
            return self.gen_dom_discount

    @domestic_discount_curve.setter
    def domestic_discount_curve(self, value):
        self._domestic_discount_curve = value

    @property
    def gen_for_discount_curve(self):
        return ForDiscountCurveGen(value_date=self.value_date_,
                                   domestic_discount_curve=self.domestic_discount_curve,
                                   fx_forward_curve=self.fx_forward_curve,
                                   curve_type=DiscountCurveType.FX_Implied).discount_curve

    @property
    def fx_forward_curve(self):
        return FXForwardCurveGen(value_date=self.value_date_,
                                 exchange_rate=self.exchange_rate,
                                 fx_swap_origin_tenors=self.get_fx_swap_data['origin_tenor'],
                                 fx_swap_quotes=self.get_fx_swap_data['swap_point']).discount_curve

    @property
    def foreign_discount_curve(self):
        if self._foreign_discount_curve:
            return self._foreign_discount_curve
        else:
            return self.gen_for_discount_curve

    @foreign_discount_curve.setter
    def foreign_discount_curve(self, value):
        self._foreign_discount_curve = value

    @property
    def volatility_surface(self):
        if self.underlier_symbol:
            return FXVolSurfaceGen(value_date=self.value_date_,
                                   currency_pair=self.underlier_symbol,
                                   exchange_rate=self.exchange_rate,
                                   domestic_discount_curve=self.domestic_discount_curve,
                                   foreign_discount_curve=self.foreign_discount_curve,
                                   fx_forward_curve=self.fx_forward_curve,
                                   tenors=self.get_fx_implied_vol_data["tenor"],
                                   origin_tenors=self.get_fx_implied_vol_data["origin_tenor"],
                                   atm_vols=self.get_fx_implied_vol_data["ATM"],
                                   butterfly_25delta_vols=self.get_fx_implied_vol_data["25D BF"],
                                   risk_reversal_25delta_vols=self.get_fx_implied_vol_data["25D RR"],
                                   butterfly_10delta_vols=self.get_fx_implied_vol_data["10D BF"],
                                   risk_reversal_10delta_vols=self.get_fx_implied_vol_data["10D RR"],
                                   volatility_function_type=TuringVolFunctionTypes.QL).volatility_surface

    @property
    def tdel(self):
        # spot_date = self.value_date_.addWeekDays(self.spot_days)
        td = (self.expiry - self.value_date_) / gDaysInYear
        if td < 0.0:
            raise TuringError("Time to expiry must be positive.")
        td = np.maximum(td, 1e-10)
        return td

    @property
    def texp(self):
        return (self.cut_off_time - self.value_date_) / gDaysInYear

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

    @property
    def df_fwd(self):
        return self.fx_forward_curve.discount(self.expiry_ql)

    @property
    def volatility_(self):
        v = self._volatility or self.ctx_volatility or \
            self.volatility or self.volatility_surface.interp_vol(self.expiry_ql, self.strike)
        if np.all(v >= 0.0):
            v = np.maximum(v, 1e-10)
            return v
        else:
            raise TuringError("Volatility should not be negative.")

    @volatility_.setter
    def volatility_(self, value: float):
        self._volatility = value

    def vol(self):
        return self.volatility_

    def rate_domestic(self):
        return self.rd

    def rate_foreign(self):
        return self.rf

    def spot(self):
        return self.exchange_rate

    def check_underlier(self):
        if self.underlier_symbol and not self.underlier:
            if isinstance(self.underlier_symbol, Enum):
                self.underlier = Turing.get_fx_symbol_to_id(
                    _id=self.underlier_symbol.value).get('asset_id')
            else:
                self.underlier = Turing.get_fx_symbol_to_id(
                    _id=self.underlier_symbol).get('asset_id')

    def __repr__(self):
        s = to_string("Object Type", type(self).__name__)
        s += to_string("Asset Id", self.asset_id)
        s += to_string("Product Type", self.product_type)
        s += to_string("Underlier", self.underlier)
        s += to_string("Underlier Symbol", self.underlier_symbol)
        s += to_string("Notional", self.notional)
        s += to_string("Notional Currency", self.notional_currency)
        s += to_string("Strike", self.strike)
        s += to_string("Expiry", self.expiry)
        s += to_string("Cut Off Time", self.cut_off_time)
        s += to_string("Exercise Type", self.exercise_type)
        s += to_string("Option Type", self.option_type)
        s += to_string("Currency Pair", self.underlier_symbol)
        s += to_string("Start Date", self.start_date)
        s += to_string("Premium Currency", self.premium_currency)
        s += to_string("Exchange Rate", self.exchange_rate)
        s += to_string("Volatility", self.volatility_)
        return s
