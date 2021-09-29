import datetime
from abc import ABCMeta
from dataclasses import dataclass, field
from typing import List, Any
from enum import Enum

import numpy as np

from fundamental.turing_db.data import Turing
from turing_models.instruments.common import FX, Currency, CurrencyPair
from turing_models.instruments.core import InstrumentBase
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.market.curves.discount_curve_zeros import TuringDiscountCurveZeros
from turing_models.market.curves.discount_curve_fx_implied import TuringDiscountCurveFXImplied
from turing_models.market.volatility.fx_vol_surface_vv import TuringFXVolSurfaceVV
from turing_models.market.volatility.fx_vol_surface_CICC import TuringFXVolSurfaceCICC
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.utilities.error import TuringError
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.global_types import TuringOptionTypes, TuringOptionType, TuringExerciseType
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.helper_functions import to_string
from turing_models.utilities.turing_date import TuringDate
from turing_models.market.curves.curve_generation import DomDiscountCurveGen, ForDiscountCurveGen
from turing_models.market.volatility.vol_surface_generation import FXVolSurfaceGen


###############################################################################
# ALL CCY RATES MUST BE IN NUM UNITS OF DOMESTIC PER UNIT OF FOREIGN CURRENCY
# SO EURUSD = 1.30 MEANS 1.30 DOLLARS PER EURO SO DOLLAR IS THE DOMESTIC AND
# EUR IS THE FOREIGN CURRENCY
###############################################################################


error_str = "Time to expiry must be positive."
error_str2 = "Volatility should not be negative."
error_str3 = "Exchange Rate must be greater than zero."


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class FXOption(FX, InstrumentBase, metaclass=ABCMeta):
    asset_id: str = None
    product_type: str = None  # VANILLA
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
    spot_days: int = 2
    value_date: TuringDate = TuringDate(
        *(datetime.date.today().timetuple()[:3]))
    exchange_rate: float = None  # 1 unit of foreign in domestic
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

        if self.exchange_rate and np.any(self.exchange_rate <= 0.0):
            raise TuringError(error_str3)

        if not self.cut_off_time or not isinstance(self.cut_off_time, TuringDate):
            self.cut_off_time = self.expiry

        self.num_paths = 100000
        self.seed = 4242

    @property
    def option_type_(self) -> TuringOptionTypes:
        if self.option_type == "CALL" or self.option_type == TuringOptionType.CALL:
            if self.exercise_type == "EUROPEAN" or self.exercise_type == TuringExerciseType.EUROPEAN:
                return TuringOptionTypes.EUROPEAN_CALL
            else:
                raise TuringError('Please check the input of exercise_type')
        elif self.option_type == "PUT" or self.option_type == TuringOptionType.PUT:
            if self.exercise_type == "EUROPEAN" or self.exercise_type == TuringExerciseType.EUROPEAN:
                return TuringOptionTypes.EUROPEAN_PUT
            else:
                raise TuringError('Please check the input of exercise_type')
        else:
            raise TuringError('Please check the input of option_type')

    @property
    def value_date_(self):
        date = self._value_date or self.ctx_pricing_date or self.value_date
        return date if date >= self.start_date else self.start_date

    @value_date_.setter
    def value_date_(self, value: TuringDate):
        self._value_date = value

    @property
    def exchange_rate_(self):
        return self._exchange_rate or self.ctx_spot or self.exchange_rate

    @exchange_rate_.setter
    def exchange_rate_(self, value: float):
        self._exchange_rate = value

    @property
    def domestic_discount_curve(self):
        if self._domestic_discount_curve:
            return self._domestic_discount_curve
        else:
            return DomDiscountCurveGen(self.value_date_).discount_curve

    @domestic_discount_curve.setter
    def domestic_discount_curve(self, value: TuringDiscountCurve):
        self._domestic_discount_curve = value

    @property
    def foreign_discount_curve(self):
        if self._foreign_discount_curve:
            return self._foreign_discount_curve
        else:
            return ForDiscountCurveGen(currency_pair=self.underlier_symbol, value_date=self.value_date_).discount_curve

    @foreign_discount_curve.setter
    def foreign_discount_curve(self, value: TuringDiscountCurve):
        self._foreign_discount_curve = value

    @property
    def volatility_surface(self):
        if self.underlier_symbol:
            return FXVolSurfaceGen(currency_pair=self.underlier_symbol,
                                   domestic_discount_curve=self.domestic_discount_curve,
                                   foreign_discount_curve=self.foreign_discount_curve,
                                   value_date=self.value_date_).volatility_surface

    @property
    def model(self):
        return TuringModelBlackScholes(self.volatility)

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
        return (self.cut_off_time - self.value_date_) / gDaysInYear

    @property
    def rd(self):
        texp = self.texp
        domDF = self.domestic_discount_curve._df(texp)
        return -np.log(domDF) / texp

    @property
    def rf(self):
        texp = self.texp
        forDF = self.foreign_discount_curve._df(texp)
        return -np.log(forDF) / texp

    @property
    def volatility_(self):
        if self._volatility:
            v = self._volatility
        elif self.ctx_volatility:
            v = self.ctx_volatility
        elif self.volatility:
            v = self.model._volatility
        else:
            v = self.volatility_surface.volatilityFromStrikeDate(
                self.strike, self.expiry)
        if np.all(v >= 0.0):
            v = np.maximum(v, 1e-10)
            return v
        else:
            raise TuringError(error_str2)

    @volatility_.setter
    def volatility_(self, value: float):
        self._volatility = value

    def vol(self):
        return self.volatility_

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
        s += to_string("Exchange Rate", self.exchange_rate_)
        s += to_string("Volatility", self.volatility_)
        return s
